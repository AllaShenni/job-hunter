import asyncio
from datetime import datetime, timedelta, timezone

from searcher_hh import Vacancy
from config import TG_API_ID, TG_API_HASH, TELEGRAM_JOB_CHANNELS
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, relevance_score

# Сколько часов назад смотреть в каналах (покрывает интервал между запусками)
LOOKBACK_HOURS = 9


async def _read_channels() -> list[Vacancy]:
    if not TG_API_ID or not TG_API_HASH:
        return []

    try:
        from telethon import TelegramClient
        from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
    except ImportError:
        return []

    results: list[Vacancy] = []
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    async with TelegramClient("job_hunter_session", TG_API_ID, TG_API_HASH) as client:
        for channel in TELEGRAM_JOB_CHANNELS:
            try:
                async for message in client.iter_messages(channel, limit=100):
                    if not message.date or message.date < since:
                        break
                    text = message.text or ""
                    # Проверяем полный текст сообщения (заголовок + тело) + гео
                    if not text or not is_relevant(text) or not is_geo_allowed(text):
                        continue

                    vid = f"tg_{channel}_{message.id}"
                    if is_sent(vid):
                        continue

                    # Ищем ссылку в entities сообщения
                    url = ""
                    if message.entities:
                        for ent in message.entities:
                            if isinstance(ent, MessageEntityUrl):
                                url = text[ent.offset : ent.offset + ent.length]
                                break
                            if isinstance(ent, MessageEntityTextUrl):
                                url = ent.url
                                break
                    if not url:
                        url = f"https://t.me/{channel}/{message.id}"

                    title_line = text.split("\n")[0][:80]

                    v = Vacancy(
                        id=vid,
                        source=f"Telegram @{channel}",
                        title=title_line,
                        company="—",
                        salary="—",
                        snippet=text[:300],
                        url=url,
                        score=relevance_score(text),
                    )
                    results.append(v)
                    mark_sent(vid, f"tg_{channel}")
            except Exception:
                continue

    results.sort(key=lambda v: v.score, reverse=True)
    return results


def fetch_telegram_vacancies() -> list[Vacancy]:
    return asyncio.run(_read_channels())
