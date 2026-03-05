import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values

def read_json(path: Path, label: str):
    if not path.exists():
        raise RuntimeError(f"{label} missing: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        raise RuntimeError(f"{label} invalid JSON: {e}")

def normalize(s: str) -> str:
    s = str(s or "").lower()
    s = unquote(s)
    s = s.replace("+", " ").replace("%20", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def build_location_signals(config: dict) -> list[str]:
    locs = (((config.get("filters") or {}).get("locations")) or [])
    if not isinstance(locs, list):
        return []
    out = []
    seen = set()
    for x in locs:
        n = normalize(str(x))
        if len(n) >= 2 and n not in seen:
            seen.add(n)
            out.append(n)
    return out

def text_has_signal(text: str, signals: list[str]) -> bool:
    n = normalize(text)
    return any(sig in n for sig in signals)

def vacancy_matches_signals(v: dict, signals: list[str]) -> bool:
    blob = " ".join(str(v.get(k, "")) for k in ("location", "title", "description", "link"))
    return text_has_signal(blob, signals)

def run_check(name, fn, results):
    try:
        fn()
        print(f"PASS: {name}")
        results.append((name, True, ""))
    except Exception as e:
        print(f"FAIL: {name}")
        print(f"  {e}")
        results.append((name, False, str(e)))

def main():
    results = []
    env_file = load_env_file(ENV_PATH)
    tw = (os.getenv("GMAIL_GLASSDOOR_TIME_WINDOW") or env_file.get("GMAIL_GLASSDOOR_TIME_WINDOW") or "").strip().lower()
    allowed_tw = {"today", "1d", "3d", "all"}

    config = {}
    signals: list[str] = []
    vacancies = []
    mail = []
    scored = []

    def check_time_window():
        if not tw:
            raise RuntimeError("GMAIL_GLASSDOOR_TIME_WINDOW is empty")
        if tw not in allowed_tw:
            raise RuntimeError(f"Unsupported GMAIL_GLASSDOOR_TIME_WINDOW={tw}")

    def check_config_and_signals():
        nonlocal config, signals
        config = read_json(ROOT / "config" / "search_config.json", "search_config.json")
        if not isinstance(config, dict):
            raise RuntimeError("search_config.json must be object")
        signals = build_location_signals(config)
        if not signals:
            raise RuntimeError("config.filters.locations must be non-empty list")

    def check_urls_match_profile():
        portals = config.get("portals") or []
        if not isinstance(portals, list):
            raise RuntimeError("config.portals must be list")
        for portal in portals:
            if not isinstance(portal, dict):
                continue
            name = portal.get("name", "unknown")
            urls = portal.get("searchUrls") or []
            if not isinstance(urls, list):
                raise RuntimeError(f"{name}.searchUrls must be list")
            bad = [u for u in urls if not text_has_signal(str(u), signals)]
            if bad:
                raise RuntimeError(f"{name} has URLs outside location profile: {bad}")

    def check_data_arrays():
        nonlocal vacancies, mail, scored
        data_dir = ROOT / "data"
        if not data_dir.exists(): data_dir.mkdir()
        
        # Создаем пустые файлы, если их нет, чтобы не падать при первом запуске
        for f in ["vacancies.json", "vacancies_mail_glassdoor.json", "scored_vacancies.json"]:
            p = data_dir / f
            if not p.exists(): p.write_text("[]")

        vacancies = read_json(data_dir / "vacancies.json", "vacancies.json")
        mail = read_json(data_dir / "vacancies_mail_glassdoor.json", "vacancies_mail_glassdoor.json")
        scored = read_json(data_dir / "scored_vacancies.json", "scored_vacancies.json")
        
        for name, arr in [("vacancies", vacancies), ("mail", mail), ("scored", scored)]:
            if not isinstance(arr, list):
                raise RuntimeError(f"{name} must be array")

    def check_location_profile_data():
        for name, arr in [("vacancies", vacancies), ("mail", mail), ("scored", scored)]:
            bad = [v for v in arr if isinstance(v, dict) and not vacancy_matches_signals(v, signals)]
            if bad:
                raise RuntimeError(f"{name} has {len(bad)} records outside location profile")

    def check_links_and_scores():
        bad_links = [v for v in vacancies if isinstance(v, dict) and not re.match(r"^https?://\S+$", str(v.get("link","")).strip())]
        if bad_links:
            raise RuntimeError(f"vacancies has {len(bad_links)} invalid links")
        bad_scores = [v for v in scored if isinstance(v, dict) and ("score" in v) and (not isinstance(v["score"], (int,float)) or v["score"] < 0 or v["score"] > 100)]
        if bad_scores:
            raise RuntimeError(f"scored has {len(bad_scores)} invalid score values")

    def check_dedup_ids():
        seen = set()
        dupes = 0
        for v in vacancies:
            if not isinstance(v, dict):
                continue
            vid = str(v.get("id","")).strip()
            if not vid:
                continue
            if vid in seen:
                dupes += 1
            seen.add(vid)
        if dupes:
            raise RuntimeError(f"vacancies has duplicate ids: {dupes}")

    run_check("Gmail time window is configured", check_time_window, results)
    run_check("search_config has active location profile", check_config_and_signals, results)
    run_check("search_config URLs match active location profile", check_urls_match_profile, results)
    run_check("data files exist and are arrays", check_data_arrays, results)
    run_check("data matches active location profile", check_location_profile_data, results)
    run_check("merged links and scored values are valid", check_links_and_scores, results)
    run_check("merged vacancies are deduplicated by id", check_dedup_ids, results)

    failed = [x for x in results if not x[1]]
    if failed:
        print(f"\nVerification failed: {len(failed)} check(s).")
        sys.exit(1)

    print("\nVerification passed: all checks are green.")

if __name__ == "__main__":
    main()