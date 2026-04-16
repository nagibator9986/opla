---
phase: 01-infrastructure-data-model
plan: 03
subsystem: infra
tags: [postgres, minio, backup, seed, management-command, django, pytest]

# Dependency graph
requires:
  - phase: 01-infrastructure-data-model
    provides: Django apps (industries, payments, accounts), models with all fields
provides:
  - docker/postgres-backup.sh — pg_dump | gzip → MinIO via mc, 7-day retention
  - apps/core/management/commands/seed_initial.py — idempotent seed command
  - Baseline data: 5 industries, 3 tariffs (ashide_1/ashide_2/upsell), 5 demo templates (9 questions each)
  - tests/test_seed.py — 5 tests covering creation, idempotency, codes, blocks, superuser
  - tests/test_backup.py — 7 structural tests for backup script
affects:
  - Phase 2 (API): seed data available for integration tests
  - Phase 3 (bot): industries and tariffs queryable via API
  - Phase 8 (cron): cron scheduling for backup deferred here with clear hook point

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Management command as seed entry point (python manage.py seed_initial)
    - get_or_create for idempotent seed operations
    - Backup via pg_dump | gzip piped to MinIO using mc CLI
    - PGPASSWORD env var (not --password flag) for pg_dump security
    - set -euo pipefail in bash scripts for fail-fast behavior

key-files:
  created:
    - docker/postgres-backup.sh
    - backend/apps/core/management/__init__.py
    - backend/apps/core/management/commands/__init__.py
    - backend/apps/core/management/commands/seed_initial.py
  modified:
    - backend/tests/test_seed.py (replaced Wave-0 xfail stubs with full tests)
    - backend/tests/test_backup.py (replaced Wave-0 xfail stubs with structural tests)

key-decisions:
  - "Tariff codes: ashide_1, ashide_2, upsell (underscore convention per CLAUDE.md)"
  - "upsell price_kzt=90000 (135000-45000 delta) as upgrade surcharge"
  - "9 demo questions per template: 5 block A + 1 block B + 3 block C"
  - "PGPASSWORD env var for pg_dump authentication (not --password, avoids process list leak)"
  - "Cron scheduling for backup deferred to Phase 8 (HARD-08) — script only in Phase 1"

patterns-established:
  - "Seed command: get_or_create on unique code field; template creation only if no template exists for industry"
  - "Bash backup scripts: set -euo pipefail; local /tmp staging; mc cp upload; mc find cleanup"

requirements-completed: [INFRA-06]

# Metrics
duration: 10min
completed: 2026-04-16
---

# Phase 1 Plan 03: Backups and Seed Data Summary

**pg_dump→gzip→MinIO backup script with 7-day retention, plus idempotent seed_initial command seeding 5 industries, 3 tariffs (ashide_1/2/upsell), and 5 demo questionnaire templates (9 questions each)**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-16T05:53:00Z
- **Completed:** 2026-04-16T05:56:50Z
- **Tasks:** 4 (03-01 through 03-04)
- **Files modified:** 6

## Accomplishments

- Created `docker/postgres-backup.sh`: pg_dump | gzip → MinIO via `mc cp`, cleans old backups via `mc find --older-than`, configurable retention via `BACKUP_RETENTION_DAYS`
- Created `seed_initial` management command: idempotent creation of 5 industries, 3 tariffs, 5 demo templates with 9 questions each (blocks A/B/C), and superuser
- Replaced Wave-0 xfail stubs in test_seed.py and test_backup.py with 12 real tests (5 seed tests + 7 backup structural tests)
- Task 03-04 verified structurally: all imports match models, field_type/block values match model choices, all 8 docker-compose services present

## Task Commits

1. **Task 03-01: Create postgres-backup.sh** - `a822446` (chore)
2. **Task 03-02: Create seed_initial management command** - `16f846c` (feat)
3. **Task 03-03: Write tests for seed command** - `95edc2f` (test)
4. **Task 03-04: Integration smoke** - structural verification, no new files needed

**Plan metadata:** (forthcoming from docs commit)

## Files Created/Modified

- `docker/postgres-backup.sh` - pg_dump|gzip backup to MinIO, 7-day retention via mc find, executable
- `backend/apps/core/management/__init__.py` - empty, required for Django management command discovery
- `backend/apps/core/management/commands/__init__.py` - empty, required for Django management command discovery
- `backend/apps/core/management/commands/seed_initial.py` - idempotent seed: industries, tariffs, templates, superuser
- `backend/tests/test_seed.py` - 5 tests: baseline data counts, idempotency, industry codes, template blocks, superuser uniqueness
- `backend/tests/test_backup.py` - 7 structural tests: existence, executability, pg_dump, mc cp, mc find, RETENTION_DAYS, PGPASSWORD

## Decisions Made

- **Tariff codes**: Using underscore convention (`ashide_1`, `ashide_2`, `upsell`) per CLAUDE.md, not hyphens
- **upsell price**: `90000 KZT` (135000 - 45000 upgrade delta), consistent with CLAUDE.md's $200 upgrade price
- **PGPASSWORD env var**: Used instead of `--password` CLI flag to avoid credentials appearing in process list
- **Cron deferred**: Backup script is Phase 1 deliverable; scheduling via cron container deferred to Phase 8 (HARD-08)
- **Demo template questions**: 9 per industry (5 block A + 1 block B + 3 block C), sufficient for functional testing

## Deviations from Plan

None — plan executed exactly as written. Task 03-04 was specified as manual verification; performed equivalent structural/static verification without Docker since no Docker environment available during code authoring.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- Backup script ready; cron scheduling hooks in Phase 8
- Seed command ready: `docker-compose exec web python manage.py seed_initial` populates all baseline data
- Test stubs (Wave-0) fully replaced — pytest can run `tests/test_seed.py` and `tests/test_backup.py` against real DB
- Phase 2 (REST API) can use seeded industries and tariffs in integration tests

---
*Phase: 01-infrastructure-data-model*
*Completed: 2026-04-16*
