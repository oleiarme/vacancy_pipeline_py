from vacancy_pipeline_py.supabase_sync import SupabaseConfig, sync_vacancies, to_supabase_row


def test_to_supabase_row_shape():
    # ???? ?????????????: ?????????, ??? ???? ???????? ?????????
    row = to_supabase_row(
        {
            "id": "gd_1",
            "title": "SRE",
            "company": "Acme",
            "location": "Lisbon",
            "link": "https://example/job/1",
            "posted": "today",
            "score": 77,
            "source": "glassdoor",
            "relevant": True,
            "reasoning": "good fit",
        }
    )
    assert row["id"] == "gd_1"
    assert row["relevant"] is True
    assert row["score"] == 77
    assert row["source"] == "glassdoor"


def test_sync_dry_run_returns_summary():
    # ???? ?????? dry_run: ???????? ??? ??????? ????
    cfg = SupabaseConfig(url="", key="")
    vacancies = [
        {"id": "gd_1", "title": "SRE", "company": "Acme", "score": 70, "relevant": True},
        {"id": "gd_2", "title": "DevOps", "company": "Beta", "score": 61, "relevant": True},
    ]
    result = sync_vacancies(cfg, vacancies, dry_run=True)
    
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["rows_count"] == 2
    # ?????????, ??? sample ???????? ??????????????? ??????
    assert len(result["sample"]) == 2
    assert result["sample"][0]["title"] == "SRE"
