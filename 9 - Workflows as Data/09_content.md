# Module 9: Workflows as Data

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Declare business processes as versioned graphs in the database; each run is an instance of one
immutable version.

## Concepts

* Graph tables: `wf.workflow_def`, `wf.workflow_version`, `wf.workflow_node`, `wf.workflow_edge`.
* Runs: `wf.workflow_instance` and `wf.node_execution`, created by `wf.wf_repo_create_workflow_instance`
  and started by `wf.sp_start_workflow_instance`.
* Node types: ACTION, SEQUENCE, PARALLEL, IF, SWITCH, REPEAT, WHILE, FOREACH, WAIT_EVENT.
* DomainPrograms compile into graphs (`workflow_engine/domain/compiler.py`, `goliath-workflow-run --compile-only`).

## Lab sequence

1. Run GoliathApp's smoke example `workflow_engine/sql_pg/examples/docs_bootstrap_minimal_workflow.sql`
   from `.lab/GoliathApp`. It builds a SEQUENCE -> ACTION graph with `workflow.const_string`, starts an
   instance and leaves a READY task.
2. Inspect `wf.workflow_instance` and `wf.node_execution` for `DocsBootstrapConstEcho`.
3. Re-run the example. Earlier runs are history now: the example purges them through the retention
   policy that `"9 - Workflows as Data"/tests` creates for this one workflow (Module 13 explains why).

## Evidence to submit

`pytest "9 - Workflows as Data"` output and the node/edge list of the graph.

## Handoff to Module 10

A READY task is waiting. Module 10 shows who picks it up.
