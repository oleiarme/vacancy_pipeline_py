# Project Memory

## Current Priorities
1. Build Python pipeline with parity to existing Node behavior.
2. Keep strict verification-first workflow.
3. Avoid regressions during migration by incremental modules.

## Non-Negotiable Process
1. Any config/filter change -> run verification.
2. No "done" status without green verification.
3. Keep artifacts and decisions documented.

## Known Risks
1. Encoding/BOM issues in JSON files (Windows).
2. Environment drift between local and CI.
3. External integrations may fail; isolate and test with fixtures first.

## Commands
```bash
# Verify pipeline
python scripts/verify_pipeline.py

# Enable pre-commit hook
git config core.hooksPath .githooks
```
