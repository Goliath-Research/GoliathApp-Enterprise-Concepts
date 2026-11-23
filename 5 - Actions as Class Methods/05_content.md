# Module 5: Actions as Class Methods

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Treat business operations as catalog entries with typed inputs and outputs, each **owned by exactly one
class**: actions are class methods.

## Concepts

* `wf.workflow_action` lists every action the platform can run; its parameters are typed through
  `wf.data_type`.
* `"Meta".sp_derive_action_methods` derives class methods from action schemas.
* `"Meta".fn_check_action_owners()` reports `ok`, `no_owner`, `multiple_owners` or `known_duplicate`
  for every action. CI runs it through `workflow_engine/scripts/verify_action_owners.sh`.
* Python declares actions as `ActionSpec` (`goliath_app/actions/spec.py`) and publishes them through the
  `goliath.action_catalogs` entry point; `seed_action_catalog.py --use-db` writes them to the database.

## Lab sequence

1. `SELECT action_name, capability FROM wf.workflow_action ORDER BY 1;`
2. `SELECT * FROM "Meta".fn_check_action_owners();` and explain each status you see.
3. Find which class owns `workflow.const_string` (expected: `platform/Workflow`), both in
   `fn_check_action_owners()` and in `"Meta"."Methods"` (`ImplKind`, `ImplRef`).
4. Read `platform/RetentionPolicy` in `"Meta"."Methods"`: its `PurgeExpiredRuns` method is implemented by
   `wf.sp_purge_run_history` (Module 13). Retention is a class method too.

## Evidence to submit

`pytest "5 - Actions as Class Methods"` output and a short note: what would break if an action had two owners?

## Handoff to Module 6

Module 6 gives these classes a stable business vocabulary for UIs and agents.
