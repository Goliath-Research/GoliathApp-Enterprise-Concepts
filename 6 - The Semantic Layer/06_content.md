# Module 6: The Semantic Layer

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Publish a stable business vocabulary (entities, attributes, vetted requests) that portals, reports and AI
agents use instead of raw tables.

## Concepts

* Registry: `portal.semantic_namespace`, `semantic_entity`, `semantic_attribute`, `semantic_request`.
* One runner, `portal.sp_run_semantic_request`, with a whitelisted filter compiler and a
  `required_permission` per request. Organization scoping is enforced centrally.
* `portal.sp_validate_semantic_registry()` checks the registry for broken targets.
* `goliath-semantic-export` exports the catalog, and CI checks it stays in sync.

## Lab sequence

1. `SELECT namespace, code, display_name FROM portal.semantic_entity ORDER BY 1, 2;`
2. `SELECT * FROM portal.sp_validate_semantic_registry() WHERE NOT ok;` returns no rows.
3. Run GoliathApp's own descendant example,
   `workflow_engine/sql_pg/examples/descendant_acme_child_register_demo.sql` (in `.lab/GoliathApp`), and
   find the `acme_child` namespace and its menu entry.

## Evidence to submit

`pytest "6 - The Semantic Layer"` output and the list of `acme_child` registry rows.

## Handoff to Module 7

Every request runs inside a session. Module 7 shows where sessions come from.
