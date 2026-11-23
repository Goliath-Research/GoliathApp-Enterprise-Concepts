"""The GoliathApp portal (platform host) running locally against the course lab database.

Opt-in: start the portal as described in README section 5.3, then set COURSE_PORTAL_URL (for example
http://127.0.0.1:3410) and COURSE_PORTAL_DEV_LOGIN_SECRET to the same local-only value the portal was
started with. The dev login exists only for local labs and tests; it is never enabled in production.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import pytest

from course_support import lab_ids, owner, require_lab

PORTAL = os.environ.get("COURSE_PORTAL_URL", "").rstrip("/")
SECRET = os.environ.get("COURSE_PORTAL_DEV_LOGIN_SECRET", "")
COOKIE = "goliath_platform_session"

pytestmark = pytest.mark.skipif(
    not PORTAL or not SECRET, reason="set COURSE_PORTAL_URL and COURSE_PORTAL_DEV_LOGIN_SECRET to test the local portal"
)


def _call(method: str, path: str, *, token: str | None = None, body: Any = None,
          headers: dict[str, str] | None = None) -> tuple[int, Any, list[str]]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(PORTAL + path, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Cookie", f"{COOKIE}={urllib.parse.quote(token)}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None), resp.headers.get_all("Set-Cookie") or []
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            payload = json.loads(raw) if raw else None
        except ValueError:
            payload = raw.decode(errors="replace")
        return err.code, payload, err.headers.get_all("Set-Cookie") or []


def _sign_in(scope_id: int) -> str:
    status, payload, cookies = _call(
        "POST", "/api/session/dev-establish",
        headers={"X-Goliath-Dev-Login-Secret": SECRET, "X-Goliath-Dev-Login-Scope-Id": str(scope_id)},
    )
    assert status == 200, payload
    for cookie in cookies:
        name, _, rest = cookie.partition("=")
        if name.strip() == COOKIE:
            return urllib.parse.unquote(rest.split(";", 1)[0])
    raise AssertionError("portal did not set a session cookie")


@pytest.fixture(scope="module")
def operator_token() -> str:
    require_lab()
    return _sign_in(lab_ids()["scope_a"])


def test_portal_is_healthy() -> None:
    status, _, _ = _call("GET", "/api/health")
    assert status == 200


def test_signed_in_operator_and_navigation(operator_token: str) -> None:
    status, me, _ = _call("GET", "/api/session/me", token=operator_token)
    assert status == 200
    assert me["userId"] == lab_ids()["operator"]
    assert me["activeRoleName"] == "acme_child_operator"
    status, nav, _ = _call("GET", "/api/navigation", token=operator_token)
    assert status == 200 and nav


def _instruments(token: str) -> dict[str, tuple[int, dict[str, Any]]]:
    """SerialNumber -> (object id, document) for every instrument the session may list."""
    path = "/api/meta/classes/" + urllib.parse.quote("acme_child/Instrument", safe="") + "/objects"
    status, payload, _ = _call("GET", path, token=token)
    assert status == 200, payload
    found: dict[str, tuple[int, dict[str, Any]]] = {}
    for item in payload["objects"]:
        status, detail, _ = _call("GET", f"/api/meta/objects/{item['objId']}", token=token)
        assert status == 200, detail
        document = detail["object"]["document"]
        found[document["SerialNumber"]] = (int(item["objId"]), document)
    return found


def test_operator_sees_only_own_organization_instruments(operator_token: str) -> None:
    serials = set(_instruments(operator_token))
    assert {"ACME-SC-0001", "ACME-SC-0002", "ACME-TH-0001"} <= serials
    assert "BENCH-PP-0001" not in serials


def test_edit_through_portal_is_recorded_in_object_history(operator_token: str) -> None:
    obj_id, current = _instruments(operator_token)["ACME-TH-0001"]
    document = dict(current)
    document["Model"] = "Therm 10 rev B" if document.get("Model") != "Therm 10 rev B" else "Therm 10"
    status, result, _ = _call("PATCH", f"/api/meta/objects/{obj_id}", token=operator_token, body={"document": document})
    assert status == 200, result

    with owner() as conn:
        row = conn.execute(
            """SELECT "ActorUserID", "DataAfter" ->> 'Model' FROM "Meta"."ObjValuesHistory"
               WHERE "ObjID" = %s AND "ChangeKind" = 'values.update' ORDER BY "HistoryID" DESC LIMIT 1""",
            (obj_id,),
        ).fetchone()
    assert row is not None, "object history (GoliathApp PR #110) not present in this lab"
    assert row[0] == lab_ids()["operator"]
    assert row[1] == document["Model"]
