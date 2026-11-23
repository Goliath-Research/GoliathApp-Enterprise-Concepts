"""Module 12 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


import uuid  # noqa: E402

from psycopg.types.json import Jsonb  # noqa: E402


def test_draft_publish_cycle() -> None:
    name = f"acme-child-bench-{uuid.uuid4().hex[:8]} (course lab)"
    with owner() as conn:
        conn.execute("SELECT * FROM cfg.cfg_repo_upsert('site', %s, '1', 'draft', %s)", (name, Jsonb({"bench": "A"})))
        assert conn.execute("SELECT * FROM cfg.cfg_repo_get('site', %s, '1', true)", (name,)).fetchall() == []
        draft = conn.execute("SELECT status, content_hash FROM cfg.cfg_repo_get('site', %s, '1', false)", (name,)).fetchone()
        conn.execute("SELECT * FROM cfg.cfg_repo_publish('site', %s, '1')", (name,))
        published = conn.execute("SELECT status, content_hash FROM cfg.cfg_repo_get('site', %s, '1', true)", (name,)).fetchone()
    assert draft[0] == "draft"
    assert published[0] == "published"
    assert published[1] == draft[1]
