from vacancy_pipeline_py.vacancy_utils import (
    get_posted_days,
    get_vacancy_dedup_key,
    parse_posted_age,
)


def test_dedup_key_fallbacks_are_unique():
    a = {"id": "a1", "title": "", "company": "", "link": "https://a.example"}
    b = {"id": "b2", "title": None, "company": None, "link": "https://b.example"}
    c = {"id": "", "title": None, "company": None, "link": "https://c.example"}

    keys = {get_vacancy_dedup_key(a), get_vacancy_dedup_key(b), get_vacancy_dedup_key(c)}
    assert len(keys) == 3


def test_posted_parsing_urgency_and_null_safety():
    assert parse_posted_age(None)["is_urgent"] is False
    assert parse_posted_age("")["is_urgent"] is False
    assert parse_posted_age("5d")["is_urgent"] is True
    assert parse_posted_age("6d")["is_urgent"] is False
    assert parse_posted_age("12h")["is_urgent"] is True


def test_get_posted_days():
    assert get_posted_days("5d") == 5
    assert get_posted_days("12h") == 1
    assert get_posted_days("36h") == 2
    assert get_posted_days("unknown") is None

