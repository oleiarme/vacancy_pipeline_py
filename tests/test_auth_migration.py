from pathlib import Path

from vacancy_pipeline_py.cli import gmail_auth
from vacancy_pipeline_py.orchestrate import _read_gmail_token


def test_gmail_auth_resolves_legacy_files(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("VACANCY_PIPELINE_STATE_DIR", raising=False)

    credentials_path, token_path = gmail_auth.resolve_auth_paths()

    assert credentials_path == repo_root / "auth" / "credentials.json"
    assert token_path == repo_root / "auth" / "gmail_token.json"


def test_orchestrate_reads_legacy_token(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("VACANCY_PIPELINE_STATE_DIR", raising=False)

    token = _read_gmail_token()

    assert token
    assert isinstance(token, str)
