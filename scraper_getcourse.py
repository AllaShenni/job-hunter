import httpx
from bs4 import BeautifulSoup
from searcher_hh import Vacancy
from config import SEARCH_QUERIES
from storage import is_sent, mark_sent

GETCOURSE_URL = "https://getcourse.ru/jobs"
KEYWORDS = {q.lower() for q in SEARCH_QUERIES} | {
    "куратор", "модератор", "администратор", "онлайн-школ", "вебинар"
}


def _is_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def fetch_getcourse_vacancies() -> list[Vacancy]:
    results: list[Vacancy] = []

    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(
                GETCOURSE_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; job-hunter-bot/1.0)"},
            )
            resp.raise_for_status()
    except Exception:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")

    # GetCourse Jobs renders job cards — find anchors with job titles
    job_cards = soup.select("a[href*='/jobs/']")

    for card in job_cards:
        title = card.get_text(strip=True)
        if not title or not _is_relevant(title):
            continue

        href = card.get("href", "")
        url = f"https://getcourse.ru{href}" if href.startswith("/") else href
        vid = f"gc_{href.strip('/').split('/')[-1]}"

        if is_sent(vid):
            continue

        # Try to get description from parent block
        parent = card.find_parent(["div", "li", "article"])
        snippet = parent.get_text(separator=" ", strip=True)[:200] if parent else ""

        v = Vacancy(
            id=vid,
            source="GetCourse Jobs",
            title=title,
            company="GetCourse",
            salary="не указана",
            snippet=snippet,
            url=url,
        )
        results.append(v)
        mark_sent(vid, "getcourse")

    return results
