from vacancy_pipeline_py.telegram_sender import TelegramConfig, build_batch_text, send_telegram_text


def test_build_batch_text_contains_fields():
    # ???????? ???????????? ?????? ?????????
    vacancies = [
        {
            "title": "Senior Site Reliability Engineer",
            "company": "SingleStore",
            "location": "Lisbon",
            "score": 78,
            "posted": "today",
            "link": "https://example.com/job/1",
        }
    ]
    text = build_batch_text(vacancies, title="Digest")
    
    # ???????? ??????? ????????
    assert "Digest" in text
    assert "SingleStore" in text
    assert "Lisbon" in text
    assert "78%" in text
    assert "https://example.com/job/1" in text


def test_send_telegram_dry_run_returns_payload():
    # ???????? ???????????? payload ??? Telegram API ??? ???????? ???????
    cfg = TelegramConfig(bot_token="dummy_token", chat_id="12345", topic_id="10")
    result = send_telegram_text(cfg, "hello", dry_run=True)
    
    assert result["ok"] is True
    assert result["dry_run"] is True
    
    payload = result["payload"]
    assert payload["chat_id"] == "12345"
    assert payload["text"] == "hello"
    # ???????? ?????????? ???????? topic_id (message_thread_id)
    assert payload["message_thread_id"] == "10" or payload["message_thread_id"] == 10
