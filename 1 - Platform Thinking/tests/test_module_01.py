"""Module 1 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


def test_platform_has_no_descendant_classes_in_platform_namespace() -> None:
    with owner() as conn:
        rows = conn.execute(
            """SELECT "Name" FROM "Meta"."Classes" WHERE "Name" LIKE 'platform/%' AND "Name" ILIKE '%acme%'"""
        ).fetchall()
    assert rows == []


def test_descendant_classes_hang_under_platform_parents() -> None:
    with owner() as conn:
        rows = dict(conn.execute(
            """SELECT c."Name", p."Name" FROM "Meta"."Classes" c JOIN "Meta"."Classes" p ON p."ID" = c."ParentID"
               WHERE c."Name" LIKE 'acme_child/%'"""
        ).fetchall())
    assert rows["acme_child/Instrument"] == "platform/Item"
    assert rows["acme_child/CalibrationRun"] == "platform/Batch"
