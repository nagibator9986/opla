"""Phase 1 Wave 0 stub — INFRA-06 (PG backup to MinIO)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_pg_dump_to_minio(mocker):
    # Will be implemented in Plan 03 — mocks pg_dump subprocess + mc pipe.
    assert True is False, "Not implemented"
