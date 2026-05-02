import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
CHAT_ID: str = os.environ["CHAT_ID"]
SUPERJOB_API_KEY: str = os.getenv("SUPERJOB_API_KEY", "")
TG_API_ID: int = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH: str = os.getenv("TG_API_HASH", "")

# Запросы к API — короткие ключевые слова (найдут вакансии по заголовку И телу)
SEARCH_QUERIES: list[str] = [
    "куратор студентов",
    "куратор онлайн",
    "куратор курсов",
    "куратор образовательных программ",
    "куратор обучения",
    "тьютор",
    "тьютор обучения",
    "наставник студентов",
    "ассистент куратора",
    "помощник куратора",
    "модератор вебинаров",
    "администратор онлайн-школы",
    "менеджер онлайн-школы",
    "менеджер отдела заботы",
    "менеджер по сопровождению",
    "менеджер по работе со студентами",
    "специалист по сопровождению студентов",
    "координатор курсов",
    "координатор обучения",
    "специалист поддержки студентов",
    "служба заботы",
    "менеджер службы заботы",
    "администратор",
    "менеджер",
    "помощник",
    "консультант",
    "student success manager",
    "community manager edtech",
    "learning coordinator",
    "online school administrator",
    "webinar moderator",
    "customer success edtech",
]

# Слова, которые ДОЛЖНЫ быть в теле вакансии — для финальной фильтрации
# Хотя бы одно из этих слов должно присутствовать
BODY_KEYWORDS: list[str] = [
    "куратор", "модератор", "онлайн-школ", "вебинар", "edtech",
    "студент", "обучени", "курс", "сопровожден", "заботы",
    "learning", "student", "webinar", "curator", "moderator",
    "e-learning", "online school", "lms", "getcourse", "геткурс",
    "образовательн", "дистанционн",
]

# Навыки Аллы — для точного матча в описании вакансии
SKILLS_KEYWORDS: list[str] = [
    "zoom", "getcourse", "telegram", "obs", "getkurs",
    "модерация чата", "поддержка студентов", "работа с возражениями",
    "сопровождение учеников", "онлайн трансляц",
]

HH_AREA = None       # None = вся Россия + мир (снимаем ограничение)
HH_SCHEDULE = "remote"
HH_PER_PAGE = 20

TELEGRAM_JOB_CHANNELS: list[str] = [
    # Только русскоязычные каналы. Украинский/белорусский/казахский — исключены.
    # edmarketclubjob исключён: много self-promo от соискателей, мало вакансий —
    # фильтр негативных откликов будет дольше настраивать, чем смотреть вручную.
    "edujobs",              # вакансии в образовании
    "razoom_jobs",          # EdTech международный (RU + Европа)
    "naudalenkebro",        # удалёнка широкого профиля
    "rabota_online_ru",     # удалённая работа
    "workvacancy",          # вакансии и фриланс
    "vakansii_udalenka",    # вакансии удалёнка
    "vakansii_ru",          # вакансии со всей России
    "remote_ru",            # удалённая работа
]

GETCOURSE_JOBS_URL = "https://getcourse.ru/jobs"

SCHEDULE_HOURS: list[int] = [7, 15]
TIMEZONE = "Europe/Moscow"
