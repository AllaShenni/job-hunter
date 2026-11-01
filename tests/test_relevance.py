from config import TELEGRAM_JOB_CHANNELS
from relevance import is_blocked_source, is_relevant, is_scam

CURATOR_VACANCY = "Ищем куратора студентов в онлайн-школу, удалённо, вебинары и чаты"


def test_curator_vacancy_is_relevant() -> None:
    assert is_relevant(CURATOR_VACANCY)


def test_influencersoffuture_channel_removed() -> None:
    assert "influencersoffuture" not in TELEGRAM_JOB_CHANNELS


def test_repost_from_blocked_source_is_rejected() -> None:
    text = f"{CURATOR_VACANCY}\nИсточник: @influencersoffuture"
    assert is_blocked_source(text)
    assert not is_relevant(text)


def test_blocked_source_matches_channel_title() -> None:
    assert is_blocked_source("Инфлюенсеры будущего")


def test_like_farming_post_is_scam() -> None:
    text = "Требуется ставить лайки на товары Ozon, обучение курс бесплатно"
    assert is_scam(text)
    assert not is_relevant(text)


def test_daily_pay_bait_is_scam() -> None:
    assert is_scam("Онлайн-работа для студентов, 3 000–5 000 ₽ в день")


def test_normal_vacancy_is_not_scam() -> None:
    assert not is_scam(CURATOR_VACANCY)
