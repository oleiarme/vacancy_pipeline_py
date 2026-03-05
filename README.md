# vacancy_pipeline_py

Python-first vacancy pipeline package.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
git config core.hooksPath .githooks
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
git config core.hooksPath .githooks
```

## Main Commands

- `vacancy-orchestrate --source fixture`
- `vacancy-orchestrate --source gmail`
- `vacancy-send-telegram`
- `vacancy-sync-supabase`
- `vacancy-verify`
- `vacancy-gmail-auth`
- `vacancy-dual-run-diff`

## Project Layout

- `src/vacancy_pipeline_py/`: production package
- `tests/`: automated tests and fixtures
- `config/`: committed configuration
- `docs/`: operational docs and plans
- `var/`: local runtime state, generated at runtime, gitignored

## Verification

```bash
pytest -q
vacancy-verify
```

## Ops Docs

- `RUNBOOK.md`
