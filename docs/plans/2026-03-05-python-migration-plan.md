# Python Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the repository into a packaged Python project with CLI entry points, centralized runtime paths, and clean CI/runtime separation.

**Architecture:** Keep the existing domain modules under `src/vacancy_pipeline_py`, add a thin `cli/` package plus `paths.py` and `settings.py`, and move generated files into `var/`. CI and local hooks will use installed console scripts rather than direct file execution.

**Tech Stack:** Python 3.13, setuptools, pytest, GitHub Actions

---

### Task 1: Add Packaging and CLI Entry Points

**Files:**
- Create: `pyproject.toml`
- Create: `src/vacancy_pipeline_py/cli/__init__.py`
- Create: `src/vacancy_pipeline_py/cli/orchestrate.py`
- Create: `src/vacancy_pipeline_py/cli/send_telegram.py`
- Create: `src/vacancy_pipeline_py/cli/sync_supabase.py`
- Create: `src/vacancy_pipeline_py/cli/verify.py`
- Modify: `src/vacancy_pipeline_py/__init__.py`
- Test: `tests/test_cli_entrypoints.py`

**Step 1: Write the failing test**

Add tests that import the new CLI modules and verify they expose `main()` functions callable without `sys.path` manipulation.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_entrypoints.py -q`
Expected: FAIL because CLI modules do not exist yet.

**Step 3: Write minimal implementation**

- Add `pyproject.toml` with package metadata and console scripts.
- Create CLI modules that parse arguments and call existing package functions.
- Export package version or package symbol cleanly from `__init__.py`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_entrypoints.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/vacancy_pipeline_py/cli src/vacancy_pipeline_py/__init__.py tests/test_cli_entrypoints.py
git commit -m "feat: add packaged cli entry points"
```

### Task 2: Centralize Paths and Settings

**Files:**
- Create: `src/vacancy_pipeline_py/paths.py`
- Create: `src/vacancy_pipeline_py/settings.py`
- Modify: `src/vacancy_pipeline_py/orchestrate.py`
- Modify: `src/vacancy_pipeline_py/telegram_sender.py`
- Modify: `src/vacancy_pipeline_py/supabase_sync.py`
- Test: `tests/test_paths.py`

**Step 1: Write the failing test**

Add tests for centralized path helpers:
- runtime directories resolve under `var/`
- helper ensures parent directories exist when needed

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_paths.py -q`
Expected: FAIL because `paths.py` does not exist yet.

**Step 3: Write minimal implementation**

- Add path constants and helper functions in `paths.py`.
- Add `.env` loading helpers in `settings.py`.
- Refactor package modules to import centralized paths/settings instead of hardcoded repo-relative definitions.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_paths.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/vacancy_pipeline_py/paths.py src/vacancy_pipeline_py/settings.py src/vacancy_pipeline_py/orchestrate.py src/vacancy_pipeline_py/telegram_sender.py src/vacancy_pipeline_py/supabase_sync.py tests/test_paths.py
git commit -m "refactor: centralize project paths and settings"
```

### Task 3: Move Runtime Artifacts to `var/`

**Files:**
- Modify: `src/vacancy_pipeline_py/orchestrate.py`
- Modify: `src/vacancy_pipeline_py/cli/send_telegram.py`
- Modify: `src/vacancy_pipeline_py/cli/sync_supabase.py`
- Modify: `src/vacancy_pipeline_py/cli/verify.py`
- Modify: `tests/test_orchestrate.py`
- Modify: `tests/test_orchestrate_gmail_fallback.py`
- Modify: `tests/test_supabase_sync.py`
- Modify: `tests/test_telegram_sender.py`

**Step 1: Write the failing test**

Update tests to assert runtime outputs are written under `var/data` and `var/runs`, and auth token lookup uses `var/auth`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_orchestrate.py tests/test_orchestrate_gmail_fallback.py tests/test_supabase_sync.py tests/test_telegram_sender.py -q`
Expected: FAIL because code still writes to old locations.

**Step 3: Write minimal implementation**

- Point runtime file reads and writes to `var/`.
- Ensure directories are created automatically.
- Keep config and test fixtures in their existing deterministic locations.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_orchestrate.py tests/test_orchestrate_gmail_fallback.py tests/test_supabase_sync.py tests/test_telegram_sender.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/vacancy_pipeline_py tests
git commit -m "refactor: move runtime artifacts under var"
```

### Task 4: Update Repo Tooling and Documentation

**Files:**
- Modify: `.github/workflows/verify-pipeline.yml`
- Modify: `.githooks/pre-commit`
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `RUNBOOK.md`
- Create: `.env.example`

**Step 1: Write the failing test**

Add or update a test that validates the verification CLI can be imported and executed, and manually inspect workflow commands for package install usage.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_entrypoints.py -q`
Expected: FAIL if verification CLI is not aligned with new settings and paths.

**Step 3: Write minimal implementation**

- Update CI to install with `pip install -e .[dev]`.
- Run `pytest -q` and `vacancy-verify`.
- Update pre-commit to use the CLI command.
- Document install, run, and runtime locations.
- Add `.env.example`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_entrypoints.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add .github/workflows/verify-pipeline.yml .githooks/pre-commit .gitignore README.md RUNBOOK.md .env.example tests/test_cli_entrypoints.py
git commit -m "chore: align ci hooks and docs with packaged project"
```

### Task 5: Remove Legacy Script Entry Points and Verify End-to-End

**Files:**
- Delete: `scripts/orchestrate.py`
- Delete: `scripts/send_telegram.py`
- Delete: `scripts/sync_supabase.py`
- Delete: `scripts/verify_pipeline.py`
- Delete: `scripts/.gitkeep`
- Modify: `pytest.ini` if needed

**Step 1: Write the failing test**

Add or update tests to rely only on package imports and CLI modules, ensuring no production path depends on `scripts/`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests -q`
Expected: FAIL if any code or tests still reference `scripts/`.

**Step 3: Write minimal implementation**

- Remove obsolete scripts.
- Fix any remaining references.
- Ensure project commands work through installed entry points only.

**Step 4: Run test to verify it passes**

Run: `python -m pytest -q`
Expected: PASS

Run: `python -m vacancy_pipeline_py.cli.verify`
Expected: successful verification output

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove legacy scripts and finalize python migration"
```
