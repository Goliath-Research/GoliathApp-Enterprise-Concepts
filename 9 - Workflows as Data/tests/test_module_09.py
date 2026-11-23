"""Module 9 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

from course_support import owner, require_lab

pytestmark = pytest.mark.usefixtures("lab")


@pytest.fixture(scope="module")
def lab() -> None:
    require_lab()


from course_support import run_example_sql  # noqa: E402


def test_minimal_workflow_example_runs_twice() -> None:
    with owner() as conn:
        if conn.execute("SELECT to_regclass('wf.run_history')").fetchone()[0] is not None:
            # Lab only: runs are history; let this one demo workflow be purged right away (Module 13).
            conn.execute(
                """SELECT "Meta".sp_obj_insert((SELECT "ID" FROM "Meta"."Classes" WHERE "Name" = 'platform/RetentionPolicy'),
                     jsonb_build_object('Label', 'Module 9 demo runs (course lab)', 'RecordKind', 'wf.run',
                                        'WorkflowName', 'DocsBootstrapConstEcho', 'RetentionDays', 0, 'LegalHold', false))
                   WHERE NOT EXISTS (SELECT 1 FROM "Meta"."ObjValues" v
                     WHERE v."Data" ->> 'Label' = 'Module 9 demo runs (course lab)')"""
            )
    for _ in range(2):
        run_example_sql("docs_bootstrap_minimal_workflow.sql")
    with owner() as conn:
        rows = conn.execute(
            """SELECT ne.status FROM wf.workflow_instance wi
               JOIN wf.workflow_version v ON v.id = wi.workflow_version_id
               JOIN wf.workflow_def d ON d.id = v.workflow_def_id
               JOIN wf.node_execution ne ON ne.workflow_instance_id = wi.id
               WHERE d.name = 'DocsBootstrapConstEcho'"""
        ).fetchall()
    assert ("READY",) in rows
