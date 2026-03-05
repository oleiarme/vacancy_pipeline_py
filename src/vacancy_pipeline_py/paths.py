from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    return repo_root() / "config"


def fixtures_dir() -> Path:
    return repo_root() / "tests" / "fixtures"


def state_dir() -> Path:
    override = os.getenv("VACANCY_PIPELINE_STATE_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return repo_root() / "var"


def data_dir() -> Path:
    return state_dir() / "data"


def runs_dir() -> Path:
    return state_dir() / "runs"


def auth_dir() -> Path:
    return state_dir() / "auth"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def env_file_path() -> Path:
    return repo_root() / ".env"


def search_config_path() -> Path:
    return config_dir() / "search_config.json"


def fixture_html_path() -> Path:
    return fixtures_dir() / "email_jobs_sample.html"


def gmail_token_path() -> Path:
    return auth_dir() / "gmail_token.json"


def gmail_credentials_path() -> Path:
    return auth_dir() / "credentials.json"


def vacancies_mail_path() -> Path:
    return data_dir() / "vacancies_mail_glassdoor.json"


def vacancies_scrape_glassdoor_path() -> Path:
    return data_dir() / "vacancies_scrape_glassdoor.json"


def vacancies_scrape_linkedin_path() -> Path:
    return data_dir() / "vacancies_scrape_linkedin.json"


def merged_vacancies_path() -> Path:
    return data_dir() / "vacancies.json"


def scored_vacancies_path() -> Path:
    return data_dir() / "scored_vacancies.json"


def last_run_path() -> Path:
    return data_dir() / "last_run.json"


def run_summary_path(run_id: str) -> Path:
    return runs_dir() / f"run_{run_id}.json"
