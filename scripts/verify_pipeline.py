import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(path: Path, label: str):
    if not path.exists():
        raise RuntimeError(f"{label} missing: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        raise RuntimeError(f"{label} invalid JSON: {e}")

def check(name, fn, results):
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

    config_path = ROOT / "config" / "search_config.json"
    vacancies_path = ROOT / "data" / "vacancies.json"
    mail_path = ROOT / "data" / "vacancies_mail_glassdoor.json"
    scored_path = ROOT / "data" / "scored_vacancies.json"

    config = {}

    def check_config():
        nonlocal config
        config = read_json(config_path, "search_config.json")
        if not isinstance(config, dict):
            raise RuntimeError("config must be object")
        locs = (((config.get("filters") or {}).get("locations")) or [])
        if not isinstance(locs, list) or not locs:
            raise RuntimeError("config.filters.locations must be non-empty list")

    def check_data_arrays():
        for p, label in [
            (vacancies_path, "vacancies.json"),
            (mail_path, "vacancies_mail_glassdoor.json"),
            (scored_path, "scored_vacancies.json"),
        ]:
            data = read_json(p, label)
            if not isinstance(data, list):
                raise RuntimeError(f"{label} must be array")

    def check_scored_shape():
        scored = read_json(scored_path, "scored_vacancies.json")
        for i, row in enumerate(scored):
            if not isinstance(row, dict):
                raise RuntimeError(f"scored[{i}] must be object")
            if "id" in row and str(row["id"]).strip() == "":
                raise RuntimeError(f"scored[{i}] has empty id")
            if "score" in row:
                s = row["score"]
                if not isinstance(s, (int, float)) or s < 0 or s > 100:
                    raise RuntimeError(f"scored[{i}] invalid score: {s}")

    check("search_config exists and has locations", check_config, results)
    check("data files exist and are arrays", check_data_arrays, results)
    check("scored file shape is valid", check_scored_shape, results)

    failed = [r for r in results if not r[1]]
    if failed:
        print(f"\nVerification failed: {len(failed)} check(s).")
        sys.exit(1)

    print("\nVerification passed: all checks are green.")

if __name__ == "__main__":
    main()
