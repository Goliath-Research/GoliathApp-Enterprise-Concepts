"""Module 11 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import has_function, owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import uuid  # noqa: E402


def test_event_ingest_is_idempotent_and_ledgered() -> None:
    key = f"course-{uuid.uuid4()}"
    with owner() as conn:
        first = conn.execute(
            "SELECT event_id, duplicate FROM wf.sp_ingest_event("
            "'course.lab.reading', 'acme_child-bench (course lab)', %s, '{\"value\": 1}')",
            (key,),
        ).fetchone()
        second = conn.execute(
            "SELECT event_id, duplicate FROM wf.sp_ingest_event("
            "'course.lab.reading', 'acme_child-bench (course lab)', %s, '{\"value\": 1}')",
            (key,),
        ).fetchone()
        assert first[1] is False
        assert second == (first[0], True)
        if has_function(conn, "portal.fn_ledger_verify(text)"):
            assert conn.execute("SELECT * FROM portal.fn_ledger_verify('wf.event')").fetchall() == []
