from vacancy_pipeline_py.scoring import score_vacancies


def test_scoring_output_shape_and_bounds():
    # ?????? ??? ?????: ???? ????????? ???? ? ???? ??????
    vacancies = [
        {
            "id": "gd_1",
            "title": "Senior Site Reliability Engineer",
            "company": "Example",
            "location": "Lisbon",
            "description": "Kubernetes Terraform AWS Linux Python CI/CD observability",
            "rating": 4.2,
            "link": "https://example.com/1",
            "source": "glassdoor",
        },
        {
            "id": "gd_2",
            "title": "Backend Developer",
            "company": "Example2",
            "location": "Berlin",
            "description": "",
            "rating": 2.9,
            "link": "https://example.com/2",
            "source": "glassdoor",
        },
    ]

    scored = score_vacancies(vacancies)
    assert len(scored) == 2

    for row in scored:
        # ???????? ????? ? ??????
        assert isinstance(row["score"], (int, float))
        assert 0 <= row["score"] <= 100
        assert isinstance(row["relevant"], bool)
        assert isinstance(row["reasoning"], str)
        assert row["reasoning"].strip() != ""

    # ???????? ??????-??????: 
    # SRE ? ???????? ?????? ??????? ?????? ??????, ??? Backend ??? ????????
    assert scored[0]["score"] > scored[1]["score"]
    
    # SRE (15 title + 5 location + 5 rating + 50 skills = 75) -> ?????? ???? ??????????? (>=60)
    assert scored[0]["relevant"] is True
    
    # Backend (0 title + 0 location + 0 rating + 10 no-desc = 10) -> ?? ??????????
    assert scored[1]["relevant"] is False
