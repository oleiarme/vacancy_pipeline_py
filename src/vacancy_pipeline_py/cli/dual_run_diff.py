from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from vacancy_pipeline_py import paths
from vacancy_pipeline_py.orchestrate import run as orchestrate_run
from vacancy_pipeline_py.vacancy_utils import get_vacancy_dedup_key

LOGS_DIR = paths.repo_root() / "docs" / "ops"


def _run_external(cmd: list[str], label: str) -> tuple[float, int]:
    print(f"\n>>> Running {label}...")
    started = time.time()
    result = subprocess.run(cmd, cwd=paths.repo_root(), check=False, capture_output=False)
    elapsed = round(time.time() - started, 2)
    print(f"<<< {label} done in {elapsed}s, exit={result.returncode}")
    return elapsed, result.returncode


def _load_vacancies(path: Path, label: str) -> dict[str, dict]:
    if not path.exists():
        print(f"  [WARN] {label}: {path} not found, using empty")
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        print(f"  [WARN] {label}: not a list")
        return {}
    return {get_vacancy_dedup_key(vacancy): vacancy for vacancy in data}


def _compare(node: dict, python_data: dict) -> dict:
    node_keys = set(node)
    python_keys = set(python_data)
    only_node = node_keys - python_keys
    only_python = python_keys - node_keys
    common = node_keys & python_keys

    score_diffs = []
    for key in common:
        node_score = node[key].get("score")
        python_score = python_data[key].get("score")
        if node_score is not None and python_score is not None and abs(float(node_score) - float(python_score)) > 5:
            score_diffs.append({"key": key, "node_score": node_score, "python_score": python_score})

    return {
        "node_total": len(node),
        "python_total": len(python_data),
        "common": len(common),
        "only_node": sorted(only_node),
        "only_python": sorted(only_python),
        "score_diffs": score_diffs,
    }


def _append_log(report: dict, elapsed_node: float, elapsed_python: float) -> None:
    paths.ensure_dir(LOGS_DIR)
    log_path = LOGS_DIR / "dual-run-log.md"
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    status = "OK" if not report["only_node"] and not report["only_python"] else "DIFF"
    row = (
        f"| {date} "
        f"| {report['node_total']} "
        f"| {report['python_total']} "
        f"| +{len(report['only_python'])}/-{len(report['only_node'])} "
        f"| {elapsed_node}s / {elapsed_python}s "
        f"| {status} |\n"
    )
    if not log_path.exists():
        log_path.write_text(
            "# Dual-Run Log\n\n"
            "| Date | Node | Python | Diff (+py/-node) | Time (N/P) | Status |\n"
            "|------|------|--------|-----------------|------------|--------|\n",
            encoding="utf-8",
        )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(row)
    print(f"\nLog updated: {log_path}")


def main() -> None:
    node_out = paths.data_dir() / "vacancies_node_snapshot.json"
    python_out = paths.data_dir() / "vacancies_python_snapshot.json"
    report_path = paths.data_dir() / "dual_run_report.json"

    elapsed_node, _ = _run_external(["node", "index.js"], "Node pipeline")
    if paths.merged_vacancies_path().exists():
        paths.ensure_parent(node_out)
        node_out.write_text(paths.merged_vacancies_path().read_text(encoding="utf-8-sig"), encoding="utf-8")

    started_python = time.time()
    orchestrate_run()
    elapsed_python = round(time.time() - started_python, 2)
    if paths.merged_vacancies_path().exists():
        paths.ensure_parent(python_out)
        python_out.write_text(paths.merged_vacancies_path().read_text(encoding="utf-8-sig"), encoding="utf-8")

    print("\n=== Comparing outputs ===")
    node_data = _load_vacancies(node_out, "node")
    python_data = _load_vacancies(python_out, "python")
    report = _compare(node_data, python_data)

    print(f"  Node total   : {report['node_total']}")
    print(f"  Python total : {report['python_total']}")
    print(f"  Common keys  : {report['common']}")
    print(f"  Only in Node : {len(report['only_node'])}")
    print(f"  Only in Py   : {len(report['only_python'])}")
    print(f"  Score diffs  : {len(report['score_diffs'])}")

    if report["only_node"]:
        print("\n  Missing in Python:")
        for key in report["only_node"][:10]:
            print(f"    - {key}")

    if report["only_python"]:
        print("\n  Extra in Python:")
        for key in report["only_python"][:10]:
            print(f"    + {key}")

    if report["score_diffs"]:
        print("\n  Score divergence (>5 pts):")
        for diff in report["score_diffs"][:10]:
            print(f"    {diff['key']}: node={diff['node_score']} py={diff['python_score']}")

    _append_log(report, elapsed_node, elapsed_python)
    paths.ensure_parent(report_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Full report: {report_path}")


if __name__ == "__main__":
    main()
