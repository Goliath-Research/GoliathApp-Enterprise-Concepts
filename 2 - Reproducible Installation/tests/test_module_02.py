"""Module 2 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import lab_ids, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import psycopg  # noqa: E402


def test_schema_is_installed_and_seeded() -> None:
    with owner() as conn:
        assert conn.execute("SELECT count(*) FROM wf.workflow_action").fetchone()[0] >= 14
        assert conn.execute('SELECT count(*) FROM portal."NavTree"').fetchone()[0] > 0
        assert conn.execute("SELECT count(*) FROM portal.semantic_entity").fetchone()[0] > 0


def test_postgres_major_version_is_academy_standard() -> None:
    with owner() as conn:
        major = int(conn.execute("SHOW server_version_num").fetchone()[0]) // 10000
    assert 18 <= major < 20


def test_portal_role_has_no_table_access() -> None:
    with portal() as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute('SELECT * FROM "RBAC"."Users"')


def test_course_data_is_labelled() -> None:
    with owner() as conn:
        names = [r[0] for r in conn.execute(
            'SELECT "Name" FROM portal."Organizations" WHERE "ID" = ANY(%s)', ([lab_ids()["org_a"], lab_ids()["org_b"]],)
        ).fetchall()]
        emails = [r[0] for r in conn.execute(
            'SELECT email FROM "RBAC"."Users" WHERE "ID" = ANY(%s)',
            ([lab_ids()[k] for k in ("admin", "operator", "outsider")],),
        ).fetchall()]
    assert names and all("(course lab)" in n for n in names)
    assert emails and all(e.endswith(".invalid") for e in emails)
