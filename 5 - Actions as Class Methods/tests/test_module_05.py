"""Module 5 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


def test_every_action_has_one_owner() -> None:
    with owner() as conn:
        statuses = dict(conn.execute('SELECT action_name, status FROM "Meta".fn_check_action_owners()').fetchall())
    assert statuses
    assert not [a for a, s in statuses.items() if s in ("no_owner", "multiple_owners")]


def test_retention_purge_is_a_class_method() -> None:
    with owner() as conn:
        if conn.execute("""SELECT 1 FROM "Meta"."Classes" WHERE "Name" = 'platform/RetentionPolicy'""").fetchone() is None:
            pytest.skip("GoliathApp without run retention (PR #111)")
        rows = conn.execute(
            """SELECT m."Name" FROM "Meta"."Methods" m JOIN "Meta"."Classes" c ON c."ID" = m."ClassID"
               WHERE c."Name" = 'platform/RetentionPolicy'"""
        ).fetchall()
    assert ("PurgeExpiredRuns",) in rows
