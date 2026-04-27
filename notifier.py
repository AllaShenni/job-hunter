import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from searcher_hh import Vacancy
from config import BOT_TOKEN, CHAT_ID, TIMEZONE

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
MAX_VACANCIES_PER_REPORT = 20
MSG_CHAR_LIMIT = 4000


def _format_vacancy(n: int, v: Vacancy) -> str:
    lines = [
        f"{n}. <b>{v.title}</b> — {v.company}",
        f"   💰 {v.salary} | 📌 {v.source}",
    ]
    if v.snippet and v.snippet != "—":
        lines.append(f"   {v.snippet[:160]}…")
    lines.append(f'   <a href="{v.url}">Открыть вакансию</a>')
    return "\n".join(lines)


def _build_messages(vacancies: list[Vacancy]) -> list[str]:
    now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M МСК, %d.%m.%Y")
    header = (
        f"🔍 <b>Найдено {len(vacancies)} новых вакансий</b>\n"
        f"⏰ {now}\n\n"
    )

    chunks: list[str] = []
    current = header
    n = 1

    for v in vacancies[:MAX_VACANCIES_PER_REPORT]:
        block = _format_vacancy(n, v) + "\n\n"
        if len(current) + len(block) > MSG_CHAR_LIMIT:
            chunks.append(current)
            current = block
        else:
            current += block
        n += 1

    if current.strip():
        chunks.append(current)

    return chunks


def _send_message(text: str) -> None:
    with httpx.Client(timeout=15) as client:
        client.post(
            f"{TG_API}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        ).raise_for_status()


def send_report(vacancies: list[Vacancy]) -> None:
    if not vacancies:
        _send_message("✅ Новых подходящих вакансий не найдено.")
        return

    for msg in _build_messages(vacancies):
        _send_message(msg)


def send_error(error: str) -> None:
    _send_message(f"⚠️ Ошибка в job-hunter:\n<code>{error[:500]}</code>")
