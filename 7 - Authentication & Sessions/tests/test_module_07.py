"""Module 7 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import lab_ids, open_session, owner, portal, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import hashlib  # noqa: E402


def test_only_the_token_hash_is_stored() -> None:
    token = open_session("operator", role="acme_child_operator")
    digest = hashlib.sha256(token.encode()).digest()
    with owner() as conn:
        stored = conn.execute('SELECT count(*) FROM "RBAC"."SessionTokens" WHERE "TokenHash" = %s', (digest,)).fetchone()[0]
        raw = conn.execute(
            """SELECT count(*) FROM "RBAC"."SessionTokens" WHERE encode("TokenHash", 'escape') = %s""", (token,)
        ).fetchone()[0]
    assert stored == 1
    assert raw == 0


def test_session_resolves_to_user_and_scope() -> None:
    ids = lab_ids()
    token = open_session("operator", role="acme_child_operator")
    with portal() as conn:
        row = conn.execute("SELECT user_id, active_scope_id FROM portal.fn_session_resolve(%s)", (token,)).fetchone()
    assert row == (ids["operator"], ids["scope_a"])
