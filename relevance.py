"""
Проверяет релевантность вакансий и их гео-доступность.

Логика гео-фильтра:
  - Для русскоязычных вакансий: принимаем только те, где явно указана работа
    из любой страны/любой точки мира. Если позиция ограничена Россией — отклоняем.
  - Для англоязычных (международных) вакансий: принимаем все remote.
"""
from config import BODY_KEYWORDS, SKILLS_KEYWORDS

# Фразы, подтверждающие работу из любой точки мира
ANYWHERE_PHRASES: list[str] = [
    "из любой точки", "из любой страны", "любая страна", "любой страны",
    "из любого города", "без привязки к", "из-за рубежа", "из другой страны",
    "worldwide", "anywhere in the world", "from anywhere", "global remote",
    "fully remote", "location: anywhere", "location: worldwide",
    "работа из-за границы", "нет привязки к стране", "работать из любого места",
    "из любой точки мира", "из заграницы", "international remote",
    "за рубежом", "эмиграция ок", "эмигранты", "релоканты",
]

# Фразы, ограничивающие вакансию Россией (отклоняем)
RUSSIA_ONLY_PHRASES: list[str] = [
    "только россия", "только рф", "гражданство рф обязательно",
    "прописка в рф", "регистрация в рф", "проживание в рф обязательно",
    "только для граждан рф", "российское гражданство обязательно",
    "работа только из России", "офис в москве", "офис в санкт-петербурге",
    "работа в офисе", "в офисе", "гибридный формат",
]


def is_relevant(text: str) -> bool:
    """True если текст содержит хотя бы одно ключевое слово из BODY_KEYWORDS."""
    t = text.lower()
    return any(kw.lower() in t for kw in BODY_KEYWORDS)


def is_geo_allowed(text: str) -> bool:
    """
    True если вакансия доступна из любой страны.

    - Если найдена фраза ANYWHERE_PHRASES → True (явно указано worldwide).
    - Если найдена RUSSIA_ONLY_PHRASES → False (ограничено Россией).
    - Если ни то ни другое → True (не ограничено явно — принимаем).
    """
    t = text.lower()

    # Явный запрет на работу не из России
    if any(phrase in t for phrase in RUSSIA_ONLY_PHRASES):
        return False

    return True  # нет явных ограничений — пропускаем


def is_explicitly_worldwide(text: str) -> bool:
    """True если вакансия явно помечена как worldwide/из любой точки."""
    t = text.lower()
    return any(phrase in t for phrase in ANYWHERE_PHRASES)


def relevance_score(text: str) -> int:
    """
    Чем выше балл — тем точнее совпадение.
    Вакансии из любой точки мира получают +5 бонус.
    """
    t = text.lower()
    score = sum(1 for kw in BODY_KEYWORDS if kw.lower() in t)
    score += sum(3 for kw in SKILLS_KEYWORDS if kw.lower() in t)
    if is_explicitly_worldwide(text):
        score += 5
    return score
