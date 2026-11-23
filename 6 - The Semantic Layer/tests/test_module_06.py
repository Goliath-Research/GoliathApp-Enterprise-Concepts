"""Module 6 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


from course_support import run_example_sql  # noqa: E402


def test_semantic_registry_is_valid() -> None:
    with owner() as conn:
        bad = conn.execute("SELECT check_name, detail FROM portal.sp_validate_semantic_registry() WHERE NOT ok").fetchall()
    assert bad == []


def test_descendant_example_registers_acme_child_namespace() -> None:
    run_example_sql("descendant_acme_child_register_demo.sql")
    with owner() as conn:
        n = conn.execute("SELECT count(*) FROM portal.semantic_namespace WHERE code = 'acme_child'").fetchone()[0]
    assert n == 1
