"""Module 4 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import class_id, open_session, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import psycopg  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402


def test_class_publishes_json_schema_with_required_serial() -> None:
    with owner() as conn:
        schema = conn.execute(
            'SELECT "Meta".fn_class_json_schema(%s, true)', (class_id(conn, "acme_child/Instrument"),)
        ).fetchone()[0]
    assert "SerialNumber" in schema.get("required", [])


@pytest.mark.parametrize(
    "doc",
    [
        {"Label": "Unknown key (course lab)", "SerialNumber": "ACME-X-1", "Colour": "red"},
        {"Label": "Missing serial (course lab)"},
    ],
)
def test_invalid_documents_are_rejected(doc: dict[str, object]) -> None:
    token = open_session("operator", role="acme_child_operator")
    with portal() as conn, pytest.raises(psycopg.Error):
        conn.execute("SELECT portal.sp_session_meta_obj_insert(%s, 'acme_child/Instrument', %s)", (token, Jsonb(doc)))
