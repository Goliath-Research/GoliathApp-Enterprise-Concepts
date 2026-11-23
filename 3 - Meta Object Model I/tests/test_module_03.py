"""Module 3 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import class_id, open_session, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


def test_instrument_lineage_reaches_platform_entity() -> None:
    with owner() as conn:
        cid = class_id(conn, "acme_child/Instrument")
        ancestors = {r[0] for r in conn.execute(
            """SELECT a."Name" FROM "Meta"."ClassClosure" cc JOIN "Meta"."Classes" a ON a."ID" = cc."AncestorID"
               WHERE cc."DescendantID" = %s""", (cid,)
        ).fetchall()}
    assert {"platform/Item", "platform/Entity"} <= ancestors


def test_polymorphic_item_query_finds_instruments() -> None:
    with owner() as conn:
        item = class_id(conn, "platform/Item")
        n = conn.execute(
            """SELECT count(*) FROM "Meta"."Objs" o
               JOIN "Meta"."ClassClosure" cc ON cc."DescendantID" = o."ClassID"
               JOIN "Meta"."Classes" c ON c."ID" = o."ClassID"
               WHERE cc."AncestorID" = %s AND c."Name" = 'acme_child/Instrument'""", (item,)
        ).fetchone()[0]
    assert n >= 4


def test_operator_reads_merged_instrument_document() -> None:
    token = open_session("operator", role="acme_child_operator")
    with portal() as conn:
        with owner() as o:
            obj = o.execute(
                """SELECT v."ObjID" FROM "Meta"."ObjValues" v WHERE v."Data" ->> 'SerialNumber' = 'ACME-SC-0001'"""
            ).fetchone()[0]
        doc = conn.execute("SELECT document FROM portal.sp_session_meta_obj_get(%s, %s)", (token, obj)).fetchone()[0]
    assert doc["SerialNumber"] == "ACME-SC-0001"
    assert doc["Label"] == "Bench scale A (course lab)"
