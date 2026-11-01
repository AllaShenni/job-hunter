from config import TELEGRAM_JOB_CHANNELS
from relevance import (
    has_curator_signal,
    is_blocked_source,
    is_mostly_sales,
    is_mostly_teaching,
    is_rejected_title,
    is_relevant,
    is_scam,
    title_of,
)


def test_teacher_vacancy_in_genitive_is_rejected() -> None:
    text = "Образовательный центр ищет преподавателя ЕГЭ по математике, онлайн-курс"
    assert is_mostly_teaching(text)
    assert not is_relevant(text)


def test_curator_working_with_teachers_is_kept() -> None:
    text = (
        "Куратор онлайн-курса: сопровождение студентов, чат группы, вебинары, "
        "взаимодействие с преподавателями"
    )
    assert not is_mostly_teaching(text)
    assert is_relevant(text)


def test_manager_and_director_titles_are_rejected() -> None:
    assert is_rejected_title(title_of("Руководитель проекта «Лицей – Школам»\nЛицей ищет..."))
    assert is_rejected_title("Директор по продукту")
    assert is_rejected_title("Ищем преподавателя ЕГЭ")


def test_curator_title_with_boss_in_body_is_kept() -> None:
    text = "Куратор онлайн-школы\nПодчинение руководителю отдела заботы, работа с преподавателями"
    assert not is_rejected_title(title_of(text))


def test_no_sales_care_manager_is_kept() -> None:
    assert not is_mostly_sales("Менеджер отдела заботы (без продаж, EdTech)")


def test_company_named_sales_is_not_a_sales_job() -> None:
    assert not is_mostly_sales("Менеджер отдела заботы. Вакансия компании: XHUMAN Sales")


def test_telemarketing_is_sales() -> None:
    assert is_mostly_sales("Менеджер телемаркетинга в онлайн школу (Без поиска клиентов)")


def test_assistant_to_manager_is_kept() -> None:
    assert not is_rejected_title("Помощник/ассистент руководителя")


def test_marketing_post_has_no_curator_signal() -> None:
    assert not has_curator_signal("Руководитель контент-маркетинга в онлайн-школу, 250 000 ₽")


def test_pure_sales_vacancy_is_rejected() -> None:
    text = (
        "Менеджер по продажам (горячие лиды) в онлайн-школу. "
        "Задачи: звонить по заявкам, закрывать сделки, выполнять план продаж."
    )
    assert is_mostly_sales(text)
    assert not is_relevant(text)


def test_curator_vacancy_with_some_sales_is_kept() -> None:
    text = (
        "Куратор онлайн-школы. Сопровождение студентов, модерация чатов, "
        "вебинары, проверка домашних заданий, поддержка учеников. "
        "Иногда допродажи следующего курса."
    )
    assert not is_mostly_sales(text)
    assert is_relevant(text)

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
