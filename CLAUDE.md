# Job Hunter Bot

Telegram-бот для поиска вакансий. Python 3.11, GitHub Actions, SQLite.

## Stack
- Python 3.11 + venv (папка называется `venv`, не `.venv`)
- httpx, telethon, python-telegram-bot, apscheduler
- SQLite (sent_vacancies.db) — дедупликация вакансий
- GitHub Actions — запуск дважды в день (07:00 и 15:00 МСК)

## Rules

@~/.claude/rule-library/python.md
@~/.claude/rule-library/python/coding-style.md
@~/.claude/rule-library/python/security.md
@~/.claude/rule-library/common/coding-style.md

## Project conventions

- Secrets: BOT_TOKEN, CHAT_ID, TG_API_ID, TG_API_HASH, TG_STRING_SESSION — только в GitHub Secrets
- Никогда не коммитить sent_vacancies.db
- Точка входа для CI: run_once.py
- generate_session.py запускать только локально, никогда в CI
- StringSession читать через os.getenv("TG_STRING_SESSION", "").strip()
