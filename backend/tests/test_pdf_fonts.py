"""Phase 1 Wave 0 stub — INFRA-05 (Cyrillic fonts in Docker image)."""
from __future__ import annotations
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_cyrillic_fonts_available():
    if shutil.which("fc-list") is None:
        pytest.skip("fc-list not available in this environment")
    out = subprocess.check_output(["fc-list"], text=True)
    assert "Liberation" in out or "DejaVu" in out
