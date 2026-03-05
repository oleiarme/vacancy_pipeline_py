from pathlib import Path
import shutil

from vacancy_pipeline_py.cli import gmail_auth
from vacancy_pipeline_py.orchestrate import _extract_access_token, _read_gmail_token

ROOT = Path(__file__).resolve().parents[1]


def _make_temp_dir(name: str) -> Path:
    target = ROOT / ".tmp-test-state" / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_gmail_auth_resolves_legacy_files(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("VACANCY_PIPELINE_STATE_DIR", raising=False)

    credentials_path, token_path = gmail_auth.resolve_auth_paths()

    assert credentials_path == repo_root / "auth" / "credentials.json"
    assert token_path == repo_root / "auth" / "gmail_token.json"


def test_orchestrate_reads_legacy_token(monkeypatch):
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("VACANCY_PIPELINE_STATE_DIR", raising=False)
    monkeypatch.setattr(
        "vacancy_pipeline_py.orchestrate._refresh_access_token_if_possible",
        lambda path, payload: "",
    )

    token = _read_gmail_token()

    assert token
    assert isinstance(token, str)


def test_extract_access_token_uses_refresh_when_available(monkeypatch):
    token_path = _make_temp_dir("token-refresh") / "gmail_token.json"
    token_path.write_text("{}", encoding="utf-8")
    token_json = {
        "token": "stale-token",
        "refresh_token": "refresh-token",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    monkeypatch.setattr(
        "vacancy_pipeline_py.orchestrate._refresh_access_token_if_possible",
        lambda path, payload: "fresh-token",
    )

    token = _extract_access_token(token_path, token_json)

    assert token == "fresh-token"
