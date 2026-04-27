from dataclasses import dataclass
from typing import Optional
import httpx
from config import SEARCH_QUERIES, HH_SCHEDULE, HH_PER_PAGE
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, relevance_score

HH_API = "https://api.hh.ru/vacancies"
HH_VACANCY_API = "https://api.hh.ru/vacancies/{id}"
HEADERS = {"User-Agent": "job-hunter-bot/1.0 (allashenni75@gmail.com)"}


@dataclass
class Vacancy:
    id: str
    source: str
    title: str
    company: str
    salary: str
    snippet: str
    url: str
    score: int = 0


def _format_salary(salary: Optional[dict]) -> str:
    if not salary:
        return "не указана"
    lo = salary.get("from")
    hi = salary.get("to")
    cur = salary.get("currency", "RUR")
    if lo and hi:
        return f"{lo:,} – {hi:,} {cur}"
    if lo:
        return f"от {lo:,} {cur}"
    if hi:
        return f"до {hi:,} {cur}"
    return "не указана"


def _fetch_full_description(client: httpx.Client, vacancy_id: str) -> str:
    """Загружает полный текст вакансии для глубокой проверки."""
    try:
        resp = client.get(
            HH_VACANCY_API.format(id=vacancy_id),
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        description = data.get("description", "") or ""
        # description возвращается как HTML — убираем теги грубо
        import re
        description = re.sub(r"<[^>]+>", " ", description)
        return description
    except Exception:
        return ""


def fetch_hh_vacancies() -> list[Vacancy]:
    results: list[Vacancy] = []
    seen_ids: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=15) as client:
        for query in SEARCH_QUERIES:
            params: dict = {
                "text": query,
                "schedule": HH_SCHEDULE,
                "per_page": HH_PER_PAGE,
                "order_by": "publication_time",
                # area не передаём — ищем по всему миру
            }
            try:
                resp = client.get(HH_API, params=params)
                resp.raise_for_status()
                items = resp.json().get("items", [])
            except Exception:
                continue

            for item in items:
                vid = f"hh_{item['id']}"
                if vid in seen_ids or is_sent(vid):
                    continue
                seen_ids.add(vid)

                # Заголовок + сниппет из списка
                snippet_data = item.get("snippet", {})
                requirement = snippet_data.get("requirement") or ""
                responsibility = snippet_data.get("responsibility") or ""
                import re
                snippet_clean = re.sub(
                    r"<[^>]+>", " ",
                    f"{requirement} {responsibility}"
                ).strip()

                # Загружаем полное описание для проверки релевантности
                full_desc = _fetch_full_description(client, item["id"])
                full_text = f"{item['name']} {snippet_clean} {full_desc}"

                if not is_relevant(full_text):
                    continue

                # Для русскоязычных вакансий — только если доступна из любой страны
                if not is_geo_allowed(full_text):
                    continue

                score = relevance_score(full_text)
                v = Vacancy(
                    id=vid,
                    source="HH.ru",
                    title=item["name"],
                    company=item.get("employer", {}).get("name", "—"),
                    salary=_format_salary(item.get("salary")),
                    snippet=snippet_clean[:220] if snippet_clean else full_desc[:220],
                    url=item["alternate_url"],
                    score=score,
                )
                results.append(v)
                mark_sent(vid, "hh")

    # Сортируем по релевантности — самые точные совпадения вверху
    results.sort(key=lambda v: v.score, reverse=True)
    return results
