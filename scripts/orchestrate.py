import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vacancy_pipeline_py.orchestrate import run  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Vacancy Pipeline Orchestrator CLI")
    p.add_argument("--source", choices=["fixture", "gmail"], default="fixture", 
                   help="Data source: local fixture or live Gmail API")
    p.add_argument("--gmail-label", default="glassdoor", 
                   help="Gmail label to search for (default: glassdoor)")
    p.add_argument("--gmail-query", default="", 
                   help="Additional Gmail search query (e.g. 'after:2026/03/01')")
    p.add_argument("--gmail-max-emails", type=int, default=20, 
                   help="Max number of emails to process")
    p.add_argument("--no-fallback-fixture", action="store_true", 
                   help="Disable automatic fallback to fixtures if Gmail fails")
    
    args = p.parse_args()

    # ?????? ?????? ???????????? ? ??????????? ???????????
    summary = run(
        source=args.source,
        gmail_label=args.gmail_label,
        gmail_query=args.gmail_query,
        gmail_max_emails=args.gmail_max_emails,
        fallback_fixture=not args.no_fallback_fixture,
    )
    
    # ????? ????????? JSON ? stdout ??? ??????????? ??????????????? ? ???
    import dataclasses
    print(json.dumps(dataclasses.asdict(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
