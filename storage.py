import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "sent_vacancies.db"

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS sent_vacancies (
        vacancy_id TEXT PRIMARY KEY,
        source     TEXT NOT NULL,
        sent_at    TEXT NOT NULL
    )
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def is_sent(vacancy_id: str) -> bool:
    # closing() actually closes the connection; "with conn" alone only commits.
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_vacancies WHERE vacancy_id = ?", (vacancy_id,)
        ).fetchone()
    return row is not None


def mark_sent(vacancy_id: str, source: str) -> None:
    with closing(_connect()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_vacancies (vacancy_id, source, sent_at) VALUES (?, ?, ?)",
            (vacancy_id, source, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
