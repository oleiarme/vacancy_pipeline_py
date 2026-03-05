import shutil
from pathlib import Path

from vacancy_pipeline_py import paths

ROOT = Path(__file__).resolve().parents[1]


def _make_state_dir(name: str) -> Path:
    target = ROOT / ".tmp-test-state" / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_runtime_paths_default_under_var(monkeypatch):
    monkeypatch.delenv("VACANCY_PIPELINE_STATE_DIR", raising=False)

    assert paths.state_dir() == paths.repo_root() / "var"
    assert paths.data_dir() == paths.state_dir() / "data"
    assert paths.runs_dir() == paths.state_dir() / "runs"
    assert paths.auth_dir() == paths.state_dir() / "auth"

def test_runtime_paths_follow_env_override(monkeypatch):
    state_dir = _make_state_dir("paths")
    monkeypatch.setenv("VACANCY_PIPELINE_STATE_DIR", str(state_dir))

    target = paths.scored_vacancies_path()
    paths.ensure_parent(target)

    assert target == state_dir / "data" / "scored_vacancies.json"
    assert target.parent.exists()
