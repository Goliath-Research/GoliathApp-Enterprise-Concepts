"""Module 13 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import has_function, lab_ids, open_session, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")



import time  # noqa: E402
import uuid  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

import psycopg  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()
    with owner() as conn:
        if not has_function(conn, "portal.sp_session_sign(text,text,text,text,text)"):
            pytest.skip("GoliathApp older than the history features #109-#112; see lab/GOLIATHAPP_PIN")


def _new_instrument(token: str) -> int:
    serial = f"ACME-M13-{uuid.uuid4().hex[:6]}"
    with portal() as conn:
        return int(conn.execute(
            "SELECT portal.sp_session_meta_obj_insert(%s, 'acme_child/Instrument', %s)",
            (token, Jsonb({"Label": "Module 13 scale (course lab)", "SerialNumber": serial})),
        ).fetchone()[0])


def test_history_is_attributed_and_readable_as_of() -> None:
    token = open_session("operator", role="acme_child_operator")
    obj = _new_instrument(token)
    with owner() as conn:
        before = conn.execute("SELECT clock_timestamp()").fetchone()[0]
    time.sleep(0.05)
    with portal() as conn:
        doc = conn.execute("SELECT document FROM portal.sp_session_meta_obj_get(%s, %s)", (token, obj)).fetchone()[0]
        doc["Model"] = "Scale 300"
        conn.execute("SELECT * FROM portal.sp_session_meta_obj_update(%s, %s, %s)", (token, obj, Jsonb(doc)))
        hist = conn.execute(
            "SELECT change_kind, actor_user_id FROM portal.sp_session_meta_obj_history(%s, %s)", (token, obj)
        ).fetchall()
    assert hist and all(uid == lab_ids()["operator"] for _, uid in hist)
    with owner() as conn:
        then = conn.execute('SELECT "Meta".fn_merged_obj_document_as_of(%s, %s)', (obj, before)).fetchone()[0]
        now = conn.execute('SELECT "Meta".fn_merged_obj_document_as_of(%s, %s)', (obj, datetime.now(UTC))).fetchone()[0]
    assert "Model" not in then
    assert now["Model"] == "Scale 300"


def test_history_rows_cannot_be_changed() -> None:
    with owner() as conn, pytest.raises(psycopg.Error):
        conn.execute('UPDATE "Meta"."ObjValuesHistory" SET "ActorUserID" = NULL')


def test_sign_detect_change_and_protect() -> None:
    ga = open_session("admin", role="god_architect")
    meaning = "course.reviewed"
    with portal() as conn, owner() as o:
        exists = o.execute(
            """SELECT 1 FROM "Meta"."ObjValues" v WHERE v."Data" ->> 'Meaning' = %s""", (meaning,)
        ).fetchone()
        if not exists:
            conn.execute(
                "SELECT portal.sp_session_meta_obj_insert(%s, 'platform/SignatureMeaning', %s)",
                (ga, Jsonb({"Label": "Reviewed (course lab)", "Meaning": meaning})),
            )
    token = open_session("operator", role="acme_child_operator")
    obj = _new_instrument(token)
    with portal() as conn:
        sig = conn.execute(
            "SELECT content_sha256 FROM portal.sp_session_sign(%s, 'meta.object', %s, %s, 'Module 13 lab')",
            (token, str(obj), meaning),
        ).fetchone()
        assert len(sig[0]) == 64
        assert [r[0] for r in conn.execute(
            "SELECT status FROM portal.sp_session_signatures(%s, 'meta.object', %s)", (token, str(obj))
        ).fetchall()] == ["valid"]
        doc = conn.execute("SELECT document FROM portal.sp_session_meta_obj_get(%s, %s)", (token, obj)).fetchone()[0]
        doc["Model"] = "Edited after signing"
        conn.execute("SELECT * FROM portal.sp_session_meta_obj_update(%s, %s, %s)", (token, obj, Jsonb(doc)))
        assert [r[0] for r in conn.execute(
            "SELECT status FROM portal.sp_session_signatures(%s, 'meta.object', %s)", (token, str(obj))
        ).fetchall()] == ["content_changed"]
    with owner() as conn, pytest.raises(psycopg.Error):
        conn.execute('DELETE FROM "Meta"."Objs" WHERE "ID" = %s', (obj,))


def test_ledgers_verify_clean() -> None:
    with owner() as conn:
        assert conn.execute("SELECT * FROM portal.fn_ledger_verify_all()").fetchall() == []


def test_history_times_are_utc_instants_in_any_session_time_zone() -> None:
    """GoliathApp #113: timestamps are true instants, even from a session far from UTC."""
    with owner() as conn:
        if not has_function(conn, "portal.fn_utc_timestamp_violations()"):
            pytest.skip("GoliathApp older than the UTC timestamp fix #113; see lab/GOLIATHAPP_PIN")
        assert conn.execute("SELECT count(*) FROM portal.fn_utc_timestamp_violations()").fetchone()[0] == 0
    token = open_session("operator", role="acme_child_operator")
    with portal() as conn:
        conn.execute("SET TIME ZONE 'Pacific/Kiritimati'")
        obj = int(conn.execute(
            "SELECT portal.sp_session_meta_obj_insert(%s, 'acme_child/Instrument', %s)",
            (token, Jsonb({"Label": "Module 13 UTC check", "SerialNumber": f"ACME-UTC-{uuid.uuid4().hex[:6]}"})),
        ).fetchone()[0])
    with owner() as conn:
        drift = conn.execute(
            'SELECT max(abs(extract(epoch FROM h."ChangedAtUtc" - now()))) FROM "Meta"."ObjValuesHistory" h WHERE h."ObjID" = %s',
            (obj,),
        ).fetchone()[0]
    assert drift is not None and float(drift) < 300
