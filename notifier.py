from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import httpx
from searcher_hh import Vacancy
from config import BOT_TOKEN, CHAT_ID, TIMEZONE

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
MSG_CHAR_LIMIT = 4000
SNIPPET_CHARS = 160
ERROR_TAIL_LINES = 12
TOKEN_MASK = "<BOT_TOKEN>"


def redact(text: str) -> str:
    """Remove the bot token from any text (tracebacks contain the API URL)."""
    return text.replace(BOT_TOKEN, TOKEN_MASK) if BOT_TOKEN else text


def _format_vacancy(n: int, v: Vacancy) -> str:
    # Vacancy text comes from third parties: escape it, or one "<" or "&"
    # makes Telegram reject the whole HTML message.
    lines = [
        f"{n}. <b>{escape(v.title)}</b> — {escape(v.company)}",
        f"   💰 {escape(v.salary)} | 📌 {escape(v.source)}",
    ]
    if v.snippet and v.snippet != "—":
        lines.append(f"   {escape(v.snippet[:SNIPPET_CHARS])}…")
    lines.append(f'   <a href="{escape(v.url, quote=True)}">Открыть вакансию</a>')
    return "\n".join(lines)


def _build_messages(vacancies: list[Vacancy]) -> list[str]:
    """Split ALL vacancies into Telegram-sized messages.

    Every vacancy is already marked as sent, so none may be dropped here.
    """
    now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M МСК, %d.%m.%Y")
    header = (
        f"🔍 <b>Найдено {len(vacancies)} новых вакансий</b>\n"
        f"⏰ {now}\n\n"
    )

    chunks: list[str] = []
    current = header
    for n, v in enumerate(vacancies, start=1):
        block = _format_vacancy(n, v) + "\n\n"
        if len(current) + len(block) > MSG_CHAR_LIMIT:
            chunks.append(current)
            current = block
        else:
            current += block

    if current.strip():
        chunks.append(current)

    return chunks


def _send_message(text: str) -> None:
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{TG_API}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
    if resp.is_error:
        # Do not use raise_for_status(): its message contains the URL with the token.
        raise RuntimeError(f"Telegram sendMessage failed: HTTP {resp.status_code} {resp.text[:200]}")


def send_report(vacancies: list[Vacancy]) -> None:
    if not vacancies:
        _send_message("✅ Новых подходящих вакансий не найдено.")
        return

    for msg in _build_messages(vacancies):
        _send_message(msg)


def send_error(error: str) -> None:
    tail = "\n".join(redact(error).strip().splitlines()[-ERROR_TAIL_LINES:])
    _send_message(f"⚠️ Ошибка в job-hunter:\n<code>{escape(tail)}</code>")
