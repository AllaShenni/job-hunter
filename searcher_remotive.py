import httpx
from searcher_hh import Vacancy
from config import SEARCH_QUERIES
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, relevance_score

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

# Английские запросы для международного рынка
ENGLISH_QUERIES = [
    "student success",
    "student curator",
    "learning coordinator",
    "community manager education",
    "online school administrator",
    "webinar moderator",
    "customer success education",
    "e-learning coordinator",
    "course coordinator",
    "education manager",
]


def fetch_remotive_vacancies() -> list[Vacancy]:
    results: list[Vacancy] = []
    seen_ids: set[str] = set()

    with httpx.Client(timeout=15) as client:
        for query in ENGLISH_QUERIES:
            try:
                resp = client.get(
                    REMOTIVE_API,
                    params={"search": query, "limit": 20},
                )
                resp.raise_for_status()
                jobs = resp.json().get("jobs", [])
            except Exception:
                continue

            for job in jobs:
                vid = f"remotive_{job['id']}"
                if vid in seen_ids or is_sent(vid):
                    continue
                seen_ids.add(vid)

                description = job.get("description", "") or ""
                # Убираем HTML теги
                import re
                description = re.sub(r"<[^>]+>", " ", description)
                full_text = f"{job.get('title', '')} {job.get('category', '')} {description}"

                if not is_relevant(full_text):
                    continue

                v = Vacancy(
                    id=vid,
                    source="Remotive (worldwide)",
                    title=job.get("title", "—"),
                    company=job.get("company_name", "—"),
                    salary=job.get("salary", "не указана") or "не указана",
                    snippet=description[:220],
                    url=job.get("url", ""),
                    score=relevance_score(full_text) + 5,  # бонус за worldwide
                )
                results.append(v)
                mark_sent(vid, "remotive")

    results.sort(key=lambda v: v.score, reverse=True)
    return results
