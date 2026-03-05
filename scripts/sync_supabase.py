from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ??????????? ?????? ? ??????? ? ????? src
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vacancy_pipeline_py.supabase_sync import SupabaseConfig, sync_vacancies

ENV_PATH = ROOT / ".env"
SCORED_PATH = ROOT / "data" / "scored_vacancies.json"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main():
    p = argparse.ArgumentParser(description="Sync scored vacancies with Supabase database")
    p.add_argument("--send", action="store_true", help="actually send to Supabase (default: dry-run)")
    p.add_argument("--only-relevant", action="store_true", help="sync only vacancies marked as relevant")
    args = p.parse_args()

    env = load_env(ENV_PATH)
    cfg = SupabaseConfig(
        url=env.get("SUPABASE_URL", ""),
        key=env.get("SUPABASE_KEY", ""),
        table=env.get("SUPABASE_TABLE", "vacancies"),
    )

    if not SCORED_PATH.exists():
        print(f"File not found: {SCORED_PATH}")
        return

    scored = json.loads(SCORED_PATH.read_text(encoding="utf-8-sig"))
    rows = [v for v in scored if isinstance(v, dict)]

    if args.only_relevant:
        rows = [v for v in rows if bool(v.get("relevant"))]

    if args.send and (not cfg.url or not cfg.key):
        raise SystemExit("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")

    # ?????????? ?????????????
    result = sync_vacancies(cfg, rows, dry_run=not args.send)
    
    # ????? ?????????? ? ??????? JSON ??? ?????????? ? ??????? ?????????????
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
