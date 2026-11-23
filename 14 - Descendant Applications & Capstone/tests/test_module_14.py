"""Module 14 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import has_function, owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


from course_support import ROOT  # noqa: E402


def test_course_lab_rebuild_inputs_exist() -> None:
    for rel in ("compose.yaml", "compose.learner.yaml", "course_lab.py", "lab/setup_lab.py", "lab/GOLIATHAPP_PIN"):
        assert (ROOT / rel).exists(), rel


def test_off_database_checkpoint_is_available() -> None:
    with owner() as conn:
        if not has_function(conn, "portal.fn_ledger_checkpoint()"):
            pytest.skip("GoliathApp without ledgers (PR #109)")
        rows = conn.execute("SELECT * FROM portal.fn_ledger_checkpoint()").fetchall()
    assert rows
