"""
Парсер вакансий hh.ru через RSS-фид.

Зачем RSS вместо API:
hh.ru закрыл API для соискателей с 15.12.2025 — на dev.hh.ru теперь могут регистрировать
приложения только работодатели. Соискательские OAuth-приложения создать нельзя,
прямые запросы к api.hh.ru возвращают 403.

RSS-фид публичный, не требует авторизации, отдаёт XML с теми же базовыми полями
(title, link, description, pubDate). Подробное описание вакансии при необходимости
догружаем отдельным запросом по ссылке item.
"""
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx
from searcher_hh import Vacancy
from config import SEARCH_QUERIES
from storage import is_sent, mark_sent
from relevance import is_relevant, is_geo_allowed, has_mandatory_phone_calls, relevance_score

log = logging.getLogger(__name__)

RSS_URL = "https://hh.ru/search/vacancy/rss"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def _strip_html(text: str) -> str:
    """Убирает HTML-теги и лишние пробелы."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_company(description_html: str) -> str:
    """Достаёт название компании из описания: 'Вакансия компании: XXX'."""
    match = re.search(r"Вакансия компании:\s*([^<\n]+)", description_html)
    return match.group(1).strip() if match else "—"


def _extract_salary(description_html: str) -> str:
    """Достаёт уровень дохода из описания."""
    match = re.search(
        r"Предполагаемый уровень месячного дохода:\s*([^<\n]+)",
        description_html,
    )
    return match.group(1).strip() if match else "не указана"


def _extract_vacancy_id(url: str) -> str:
    """Из URL hh.ru/vacancy/12345 достаёт '12345'."""
    match = re.search(r"/vacancy/(\d+)", url)
    return match.group(1) if match else url


def _fetch_full_page(client: httpx.Client, url: str) -> str:
    """Загружает страницу вакансии для глубокой проверки релевантности и гео."""
    try:
        resp = client.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        return _strip_html(resp.text)
    except Exception as exc:
        log.warning("hh.ru page not loaded (%s): %s", url, type(exc).__name__)
        return ""


def fetch_hh_vacancies() -> list[Vacancy]:
    """Главная точка входа — совместима с прежним API-парсером."""
    results: list[Vacancy] = []
    seen_ids: set[str] = set()
    failed_queries = 0

    with httpx.Client(headers=HEADERS, timeout=15) as client:
        for query in SEARCH_QUERIES:
            params = {
                "text": query,
                "schedule": "remote",
                "order_by": "publication_time",
            }
            try:
                resp = client.get(RSS_URL, params=params)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
            except Exception as exc:
                failed_queries += 1
                log.warning("hh.ru RSS query %r failed: %s", query, type(exc).__name__)
                continue

            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc_html = item.findtext("description") or ""

                vid_raw = _extract_vacancy_id(link)
                vid = f"hh_{vid_raw}"

                if vid in seen_ids or is_sent(vid):
                    continue
                seen_ids.add(vid)

                company = _extract_company(desc_html)
                salary = _extract_salary(desc_html)
                snippet_clean = _strip_html(desc_html)

                # Релевантность и негативные роли — проверяем ТОЛЬКО по названию
                # и RSS-сниппету. Полную страницу hh.ru через эти фильтры пускать
                # нельзя: на ней в боковой панели есть похожие вакансии
                # (программист, дизайнер и т.п.), которые ложно срабатывают на
                # NEGATIVE_ROLE_KEYWORDS.
                base_text = f"{title} {snippet_clean}"
                if not is_relevant(base_text):
                    continue

                # Полную страницу используем ТОЛЬКО для проверки гео-ограничений
                # и обязательных звонков — там фразы конкретные, ложных
                # срабатываний от навигации hh.ru не случается.
                full_text = _fetch_full_page(client, link)

                if not is_geo_allowed(full_text):
                    continue
                if has_mandatory_phone_calls(full_text):
                    continue

                score = relevance_score(base_text)
                v = Vacancy(
                    id=vid,
                    source="HH.ru",
                    title=title,
                    company=company,
                    salary=salary,
                    snippet=snippet_clean[:220],
                    url=link,
                    score=score,
                )
                results.append(v)
                mark_sent(vid, "hh")

    # If every query failed, hh.ru is blocking us — surface it instead of "nothing found".
    if failed_queries == len(SEARCH_QUERIES):
        raise RuntimeError(f"hh.ru RSS: все {failed_queries} запросов завершились ошибкой")

    results.sort(key=lambda v: v.score, reverse=True)
    return results
