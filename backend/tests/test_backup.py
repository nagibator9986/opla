"""Tests for docker/postgres-backup.sh (Plan 03 — INFRA-06)."""
from __future__ import annotations

import os
import stat


BACKUP_SCRIPT = os.path.join(
    os.path.dirname(__file__),  # backend/tests/
    "..", "..", "docker", "postgres-backup.sh",
)


def test_backup_script_exists():
    assert os.path.isfile(BACKUP_SCRIPT), "docker/postgres-backup.sh must exist"


def test_backup_script_is_executable():
    st = os.stat(BACKUP_SCRIPT)
    assert st.st_mode & stat.S_IXUSR, "docker/postgres-backup.sh must be executable"


def test_backup_script_contains_pg_dump():
    with open(BACKUP_SCRIPT) as f:
        content = f.read()
    assert "pg_dump" in content


def test_backup_script_contains_mc_cp():
    with open(BACKUP_SCRIPT) as f:
        content = f.read()
    assert "mc cp" in content


def test_backup_script_contains_mc_find():
    with open(BACKUP_SCRIPT) as f:
        content = f.read()
    assert "mc find" in content


def test_backup_script_contains_retention():
    with open(BACKUP_SCRIPT) as f:
        content = f.read()
    assert "RETENTION_DAYS" in content


def test_backup_script_uses_pgpassword():
    """Ensure password is passed via env var, not CLI flag (security)."""
    with open(BACKUP_SCRIPT) as f:
        content = f.read()
    assert "PGPASSWORD" in content
    # Must NOT use --password flag (insecure: shows in process list)
    assert "--password" not in content
