from notifier import MSG_CHAR_LIMIT, _build_messages, redact
from searcher_hh import Vacancy

BOT_TOKEN = "123456:TEST_TOKEN_VALUE"


def make_vacancy(n: int, title: str = "Куратор") -> Vacancy:
    return Vacancy(
        id=f"t{n}", source="Test", title=f"{title} {n}", company="Школа & Ко",
        salary="от 50 000 ₽", snippet="Опыт <1 года ок", url=f"https://example.com/{n}", score=1,
    )


def test_special_characters_are_escaped() -> None:
    text = "".join(_build_messages([make_vacancy(1, title="A<B")]))
    assert "A&lt;B" in text
    assert "Школа &amp; Ко" in text
    assert "&lt;1 года" in text


def test_all_vacancies_are_sent_not_only_twenty() -> None:
    vacancies = [make_vacancy(n) for n in range(1, 46)]
    text = "".join(_build_messages(vacancies))
    assert "Куратор 45" in text
    assert "Куратор 21" in text


def test_messages_fit_telegram_limit() -> None:
    messages = _build_messages([make_vacancy(n) for n in range(1, 60)])
    assert all(len(m) <= MSG_CHAR_LIMIT for m in messages)


def test_token_is_redacted_from_errors() -> None:
    error = f"HTTPStatusError for url https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    assert BOT_TOKEN not in redact(error)
