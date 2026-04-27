import httpx
from searcher_hh import Vacancy
from config import SEARCH_QUERIES, SUPERJOB_API_KEY
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, relevance_score

SJ_API = "https://api.superjob.ru/2.0/vacancies/"


def fetch_superjob_vacancies() -> list[Vacancy]:
    if not SUPERJOB_API_KEY:
        return []

    results: list[Vacancy] = []
    seen_ids: set[str] = set()
    headers = {"X-Api-App-Id": SUPERJOB_API_KEY}

    with httpx.Client(timeout=15) as client:
        for query in SEARCH_QUERIES:
            try:
                resp = client.get(
                    SJ_API,
                    headers=headers,
                    params={
                        "keyword": query,
                        "place_of_work": 1,  # удалённо
                        "count": 20,
                        "order_field": "date",
                        # без area — вся Россия
                    },
                )
                resp.raise_for_status()
                items = resp.json().get("objects", [])
            except Exception:
                continue

            for item in items:
                vid = f"sj_{item['id']}"
                if vid in seen_ids or is_sent(vid):
                    continue
                seen_ids.add(vid)

                # Тело вакансии — поле vacancyRichText или candidat
                body = item.get("vacancyRichText") or item.get("candidat") or ""
                full_text = f"{item.get('profession', '')} {body}"

                if not is_relevant(full_text):
                    continue

                if not is_geo_allowed(full_text):
                    continue

                pay_from = item.get("payment_from") or 0
                pay_to = item.get("payment_to") or 0
                if pay_from and pay_to:
                    salary = f"{pay_from:,} – {pay_to:,} ₽"
                elif pay_from:
                    salary = f"от {pay_from:,} ₽"
                elif pay_to:
                    salary = f"до {pay_to:,} ₽"
                else:
                    salary = "не указана"

                v = Vacancy(
                    id=vid,
                    source="SuperJob",
                    title=item.get("profession", "—"),
                    company=item.get("firm_name", "—"),
                    salary=salary,
                    snippet=body[:220],
                    url=item.get("link", ""),
                    score=relevance_score(full_text),
                )
                results.append(v)
                mark_sent(vid, "superjob")

    results.sort(key=lambda v: v.score, reverse=True)
    return results
