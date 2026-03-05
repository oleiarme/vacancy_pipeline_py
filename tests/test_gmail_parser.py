from datetime import datetime, timezone

from vacancy_pipeline_py.gmail_parser import (
    build_location_signals,
    filter_vacancies_by_location,
    is_message_allowed_by_time_window,
    parse_job_cards_from_html,
)


def test_parse_job_cards_from_html_extracts_cards():
    # ?????? ????????. utf-8-sig ?????????? BOM, ???? ?? ??? ????
    html = open("tests/fixtures/email_jobs_sample.html", "r", encoding="utf-8").read()
    cards = parse_job_cards_from_html(html)
    assert len(cards) == 2
    assert cards[0]["title"] == "Senior Site Reliability Engineer"
    assert cards[0]["company"] == "SingleStore"
    assert cards[0]["location"] == "Lisbon"
    assert cards[0]["id"] == "gd_1010036737326"


def test_filter_vacancies_by_location_uses_active_profile():
    html = open("tests/fixtures/email_jobs_sample.html", "r", encoding="utf-8").read()
    cards = parse_job_cards_from_html(html)
    config = {"filters": {"locations": ["Portugal", "Lisbon", "Porto"]}}
    signals = build_location_signals(config)
    kept = filter_vacancies_by_location(cards, signals)
    assert len(kept) == 1
    assert kept[0]["location"] == "Lisbon"


def test_time_window_today_and_1d():
    # ????????? ????? ??? ??????????????????? ??????
    now = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    same_day = int(datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    prev_day = int(datetime(2026, 3, 9, 8, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    assert is_message_allowed_by_time_window(same_day, "today", now_utc=now) is True
    assert is_message_allowed_by_time_window(prev_day, "today", now_utc=now) is False
    # 28 ????? ??????? (? 08:00 9-?? ?? 12:00 10-??) ? ?????? ??? 1d
    assert is_message_allowed_by_time_window(prev_day, "1d", now_utc=now) is False
    assert is_message_allowed_by_time_window(prev_day, "3d", now_utc=now) is True
