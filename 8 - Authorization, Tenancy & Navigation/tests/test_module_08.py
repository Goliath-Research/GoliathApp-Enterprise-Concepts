"""Module 8 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import lab_ids, open_session, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import psycopg  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402


def _instrument(serial: str) -> int:
    with owner() as conn:
        return int(conn.execute(
            """SELECT v."ObjID" FROM "Meta"."ObjValues" v WHERE v."Data" ->> 'SerialNumber' = %s""", (serial,)
        ).fetchone()[0])


def test_outsider_cannot_read_acme_child_instrument() -> None:
    token = open_session("outsider", scope_key="scope_b", role="acme_child_operator")
    with portal() as conn, pytest.raises(psycopg.Error) as err:
        conn.execute("SELECT * FROM portal.sp_session_meta_obj_get(%s, %s)", (token, _instrument("ACME-SC-0001")))
    # Another tenant's object is reported as not found: the platform does not reveal that it exists.
    assert err.value.sqlstate == "GS404"

def test_operator_cannot_author_platform_classes() -> None:
    if not has_function_owner("platform/RetentionPolicy"):
        pytest.skip("GoliathApp without run retention (PR #111)")
    token = open_session("operator", role="acme_child_operator")
    doc = {"Label": "Not allowed (course lab)", "RecordKind": "wf.run", "RetentionDays": 1}
    with portal() as conn, pytest.raises(psycopg.Error):
        conn.execute("SELECT portal.sp_session_meta_obj_insert(%s, 'platform/RetentionPolicy', %s)", (token, Jsonb(doc)))


def test_god_architect_can_author_platform_objects() -> None:
    if not has_function_owner("platform/SignatureMeaning"):
        pytest.skip("GoliathApp without electronic signatures (PR #112)")
    token = open_session("admin", role="god_architect")
    with portal() as conn:
        obj = conn.execute(
            "SELECT portal.sp_session_meta_obj_insert(%s, 'platform/SignatureMeaning', %s)",
            (token, Jsonb({"Label": "Module 8 check (course lab)", "Meaning": "course.module8.check"})),
        ).fetchone()[0]
    with owner() as conn:
        activated = conn.execute(
            """SELECT count(*) FROM portal.session_active_role_audit a JOIN "RBAC"."Roles" r ON r."ID" = a.role_id
               WHERE r."Name" = 'god_architect' AND a.user_id = %s""", (lab_ids()["admin"],)
        ).fetchone()[0]
        attributed = None
        if conn.execute("""SELECT to_regclass('"Meta"."ObjValuesHistory"')""").fetchone()[0] is not None:
            attributed = conn.execute(
                """SELECT "ActorUserID" FROM "Meta"."ObjValuesHistory" WHERE "ObjID" = %s AND "ChangeKind" = 'object.create'""",
                (obj,),
            ).fetchone()[0]
        conn.execute('DELETE FROM "Meta"."Objs" WHERE "ID" = %s', (obj,))
    assert activated > 0
    if attributed is not None:
        assert attributed == lab_ids()["admin"]

def has_function_owner(class_name: str) -> bool:
    with owner() as conn:
        return conn.execute('SELECT 1 FROM "Meta"."Classes" WHERE "Name" = %s', (class_name,)).fetchone() is not None
