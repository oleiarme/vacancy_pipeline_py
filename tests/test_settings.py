from pathlib import Path
import shutil

from vacancy_pipeline_py.settings import get_env, load_env

ROOT = Path(__file__).resolve().parents[1]


def _make_temp_dir(name: str) -> Path:
    target = ROOT / ".tmp-test-state" / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_load_env_strips_bom_from_keys():
    env_path = _make_temp_dir("settings-load-bom") / ".env"
    env_path.write_text("\ufeffGMAIL_GLASSDOOR_TIME_WINDOW=today\nOTHER_KEY=ok\n", encoding="utf-8")

    values = load_env(env_path)

    assert "GMAIL_GLASSDOOR_TIME_WINDOW" in values
    assert values["GMAIL_GLASSDOOR_TIME_WINDOW"] == "today"
    assert values["OTHER_KEY"] == "ok"
    assert "\ufeffGMAIL_GLASSDOOR_TIME_WINDOW" not in values


def test_get_env_reads_bom_prefixed_first_key(monkeypatch):
    env_path = _make_temp_dir("settings-bom") / ".env"
    env_path.write_text("\ufeffGMAIL_GLASSDOOR_TIME_WINDOW=today\n", encoding="utf-8")
    monkeypatch.delenv("GMAIL_GLASSDOOR_TIME_WINDOW", raising=False)

    value = get_env("GMAIL_GLASSDOOR_TIME_WINDOW", env_path=env_path)

    assert value == "today"
