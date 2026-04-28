import httpx
from searcher_hh import Vacancy
from config import SEARCH_QUERIES
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, relevance_score

HABR_API = "https://career.habr.com/api/frontend/vacancies"
HABR_VACANCY = "https://career.habr.com/api/frontend/vacancies/{id}"


def _fetch_body(client: httpx.Client, vacancy_id: int) -> str:
    try:
        resp = client.get(HABR_VACANCY.format(id=vacancy_id), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("vacancy", {}).get("body", "") or ""
    except Exception:
        return ""


def fetch_habr_vacancies() -> list[Vacancy]:
    results: list[Vacancy] = []
    seen_ids: set[str] = set()

    with httpx.Client(timeout=15) as client:
        for query in SEARCH_QUERIES:
            try:
                resp = client.get(
                    HABR_API,
                    params={
                        "q": query,
                        "type": "all",
                        "remote": "true",  # только удалёнка
                        "page": 1,
                        "per_page": 20,
                        "sort": "date",
                        # без locations — весь мир
                    },
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                items = resp.json().get("list", [])
            except Exception:
                continue

            for item in items:
                vid = f"habr_{item.get('id', '')}"
                if not item.get("id") or vid in seen_ids or is_sent(vid):
                    continue
                seen_ids.add(vid)

                body = _fetch_body(client, item["id"])
                full_text = f"{item.get('title', '')} {item.get('description', '')} {body}"

                if not is_relevant(full_text):
                    continue

                if not is_geo_allowed(full_text):
                    continue

                salary_data = item.get("salary") or {}
                salary = salary_data.get("title", "не указана")

                slug = item.get("slug", "") or str(item.get("id", ""))
                url = f"https://career.habr.com/vacancies/{slug}" if slug else ""

                v = Vacancy(
                    id=vid,
                    source="Habr Career",
                    title=item.get("title", "—"),
                    company=item.get("company", {}).get("title", "—"),
                    salary=salary,
                    snippet=(item.get("description") or body)[:220],
                    url=url,
                    score=relevance_score(full_text),
                )
                results.append(v)
                mark_sent(vid, "habr")

    results.sort(key=lambda v: v.score, reverse=True)
    return results
