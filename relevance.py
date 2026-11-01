"""
Проверяет релевантность вакансий и их гео-доступность.

Логика гео-фильтра:
  - Для русскоязычных вакансий: принимаем только те, где явно указана работа
    из любой страны/любой точки мира. Если позиция ограничена Россией — отклоняем.
  - Для англоязычных (международных) вакансий: принимаем все remote.
  - Украиноязычные вакансии — отклоняем.
  - Вакансии SMM/таргетолог/контент — отклоняем.
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

# Слова-маркеры украинского языка (отклоняем украиноязычные вакансии)
UKRAINIAN_MARKERS: list[str] = [
    "вакансія", "вакансії", "робота", "потрібен", "потрібна", "потрібно",
    "досвід роботи", "обов'язки", "вимоги", "умови роботи",
    "ми шукаємо", "запрошуємо", "будемо раді", "звертайтесь",
    "офіційне працевлаштування", "дружній колектив",
    "надсилайте", "резюме на пошту", "чекаємо на вас",
    # Уникальные украинские слова (в русском: кто→хто, что→що, для тех→для тих)
    " хто ", "для тих", "відкликаються", "мрієте", "втомився",
    "закривати", "відгукнутися", "долучитися", "команді чекає",
    "підходять", "про кого", "не читають",
]

# Нерелевантные роли — отклоняем, даже если есть ключевые слова
NEGATIVE_ROLE_KEYWORDS: list[str] = [
    "smm", "смм", "smm-специалист", "smm специалист",
    "таргетолог", "таргетированная реклама", "таргет специалист",
    "social media manager", "ведение соцсетей", "ведение instagram",
    "ведение tiktok",
    "копирайтер", "копирайтинг", "seo-специалист", "seo специалист",
    "программист", "разработчик", "developer", "backend", "frontend",
    "fullstack", "devops", "data scientist", "аналитик данных",
    "дизайнер", "верстальщик", "product manager", "продакт менеджер",
    # Преподавание — отклоняем (Алла не преподаватель)
    "преподаватель", "преподавание", "учитель", "репетитор",
    "tutor", "teacher", "ментор по",
    "тренер по", "коуч по", "автор курса", "методист",
    # Банки и финансы — отклоняем
    "банк", "bank", "сбербанк", "сбер", "втб", "альфа-банк", "альфабанк",
    "тинькофф", "т-банк", "тбанк", "газпромбанк", "райффайзен",
    "росбанк", "открытие", "почта банк", "совкомбанк", "мкб",
    "кредитный", "кредитование", "ипотека", "ипотечный",
    "банковский", "банковская", "банковское", "финансовый консультант",
    "страховая", "страхование", "микрозайм", "мфо",
]

# Фразы, указывающие на обязательные звонки по обычной телефонии
# (отклоняем — из Алжира звонки через российские SIP не работают)
MANDATORY_PHONE_PHRASES: list[str] = [
    "холодные звонки",
    "холодный обзвон",
    "обзвон базы",
    "обзвон клиентов",
    "звонки — основа работы",
    "звонки - основа работы",
    "звонки основа работы",
    "не боитесь телефонных звонков",
    "не боится телефонных звонков",
    "активные звонки",
    "исходящие звонки клиентам",
    "100+ звонков",
    "звонки по холодной базе",
]


def has_mandatory_phone_calls(text: str) -> bool:
    """True если вакансия требует активного обзвона по обычной телефонии."""
    t = text.lower()
    return any(phrase in t for phrase in MANDATORY_PHONE_PHRASES)


# Фразы, явно ограничивающие вакансию Россией (отклоняем).
# Намеренно НЕ включаем общие выражения вроде "в офисе" / "гибридный формат" —
# они часто встречаются в шаблонах hh.ru и дают ложные срабатывания.
RUSSIA_ONLY_PHRASES: list[str] = [
    "только россия",
    "только рф",
    "гражданство рф обязательно",
    "только для граждан рф",
    "российское гражданство обязательно",
    "прописка в рф обязательна",
    "проживание в рф обязательно",
    "работа только из россии",
    "только из россии",
]


# Источники, которые Алла не хочет видеть — в том числе их пересылки и репосты
BLOCKED_SOURCE_MARKERS: list[str] = [
    "influencersoffuture",
    "инфлюенсеры будущего",
    "influencers of future",
]

# Типичные признаки мусорных/мошеннических объявлений в каналах удалёнки
SCAM_PHRASES: list[str] = [
    "ставить лайки", "ставить лайк", "лайкать",
    "простых задач в цифровой среде", "простые задания",
    "в день без опыта", "₽ в день", "руб в день", "рублей в день",
    "пассивный доход", "без вложений",
    "оплатить обучение", "платное обучение", "стоимость обучения",
    "предоплата", "оплатите доступ", "доступ к вакансиям",
]


# Продажи vs кураторство: Алле не нужны вакансии менеджеров по продажам,
# но нужны те, где обязанностей куратора/администратора больше, чем продаж.
SALES_MARKERS: list[str] = [
    "менеджер по продажам", "менеджера по продажам", "специалист по продажам",
    "оператор продаж", "отдел продаж", "план продаж", "продаж", "продавать",
    # "sales" only as a job title: a bare "sales" also matches company names.
    "моп", "sales manager", "head of sales", "sdr",
    "лид", "закрывать сделк", "сделк", "воронк", "конверси",
    "допродаж", "апсейл", "upsell", "холодн", "квалификация лидов",
    "телемаркетинг", "видеопродаж",
]
# Отрицания убираются из текста до подсчёта: "без продаж" — плюс, а не минус.
SALES_NEGATIONS: list[str] = [
    "без продаж", "не продаж", "нет продаж", "без звонков", "без поиска клиентов",
    "не нужно продавать", "не надо продавать", "без холодных",
]
CURATOR_MARKERS: list[str] = [
    "куратор", "курирован", "администратор", "администрирован", "модератор",
    "модерац", "вебинар", "сопровожден", "забот",
    "поддержк", "студент", "ученик", "чат", "расписани", "домашн",
    "обратная связь", "обратной связи", "техническ", "геткурс", "getcourse",
]


# Преподавание считается по корням слов: "преподавателя", "учителей" и т.п.
# Сравнивается с кураторством, а не запрещается целиком: куратору часто нужно
# "взаимодействовать с преподавателями".
TEACHING_MARKERS: list[str] = [
    "преподавател", "преподава", "учител", "репетитор",
    "провод уроки", "ведение уроков", "вести уроки",
]


# Должности, которые Алле не нужны. Проверяются ТОЛЬКО в названии вакансии:
# в теле кураторских вакансий часто есть "подчинение руководителю" и т.п.
TITLE_REJECT_MARKERS: list[str] = [
    "руководител", "директор", "head of", "director",
    "преподавател", "учител", "репетитор", "teacher",
]
# "Помощник руководителя" — ассистентская роль, она Алле подходит.
TITLE_ASSISTANT_MARKERS: list[str] = ["помощник", "ассистент", "assistant"]
BOSS_MARKERS: list[str] = ["руководител", "директор", "head of", "director"]
# Для постов Telegram названием считаем первую строку, но не длиннее этого
TITLE_ZONE_CHARS = 150


def title_of(text: str) -> str:
    """Название вакансии в посте: первая непустая строка."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    return first[:TITLE_ZONE_CHARS]


def is_rejected_title(title: str) -> bool:
    """True если в названии вакансии руководитель, директор или преподаватель."""
    t = title.lower()
    is_assistant = any(marker in t for marker in TITLE_ASSISTANT_MARKERS)
    return any(
        marker in t
        for marker in TITLE_REJECT_MARKERS
        if not (is_assistant and marker in BOSS_MARKERS)
    )


def _count_markers(text: str, markers: list[str]) -> int:
    t = text.lower()
    return sum(t.count(m) for m in markers)


def _outweighs_curator_work(text: str, markers: list[str]) -> bool:
    """True если маркеров чужой роли есть и их не меньше, чем кураторских."""
    other = _count_markers(text, markers)
    return other > 0 and other >= _count_markers(text, CURATOR_MARKERS)


def _without_negations(text: str) -> str:
    t = text.lower()
    for phrase in SALES_NEGATIONS:
        t = t.replace(phrase, " ")
    return t


def is_mostly_sales(text: str) -> bool:
    """True если вакансия про продажи и продаж в ней не меньше, чем кураторской работы."""
    return _outweighs_curator_work(_without_negations(text), SALES_MARKERS)


def is_mostly_teaching(text: str) -> bool:
    """True если вакансия про преподавание больше, чем про кураторство."""
    return _outweighs_curator_work(text, TEACHING_MARKERS)


def has_curator_signal(text: str) -> bool:
    """True если в тексте есть хоть один признак работы куратора/администратора.

    Применяется к длинным постам Telegram-каналов: отсекает маркетинг, PR,
    анонсы мероприятий. Для hh.ru не применяется — там только короткий анонс.
    """
    return _count_markers(text, CURATOR_MARKERS) > 0


def is_blocked_source(text: str) -> bool:
    """True если текст пришёл из нежелательного источника (или это его пересылка)."""
    t = text.lower()
    return any(marker in t for marker in BLOCKED_SOURCE_MARKERS)


def is_scam(text: str) -> bool:
    """True если объявление похоже на мусор или развод."""
    t = text.lower()
    return any(phrase in t for phrase in SCAM_PHRASES)


def is_ukrainian(text: str) -> bool:
    """True если текст написан на украинском языке."""
    t = text.lower()
    return sum(1 for marker in UKRAINIAN_MARKERS if marker in t) >= 2


def has_negative_role(text: str) -> bool:
    """True если вакансия относится к нерелевантным ролям (SMM, разработка, дизайн)."""
    t = text.lower()
    return any(kw.lower() in t for kw in NEGATIVE_ROLE_KEYWORDS)


def is_relevant(text: str) -> bool:
    """True если текст содержит хотя бы одно ключевое слово из BODY_KEYWORDS,
    не является украиноязычным и не относится к нерелевантным ролям."""
    if is_ukrainian(text):
        return False
    if is_blocked_source(text) or is_scam(text):
        return False
    if is_mostly_sales(text) or is_mostly_teaching(text):
        return False
    if has_negative_role(text):
        return False
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
