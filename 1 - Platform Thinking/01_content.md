# Module 1: Platform Thinking

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Understand what a **database-governed platform** is and why GoliathApp is built as one: shared mechanics
(identity, data model, workflow, audit) live in one governed core, and products extend it with data and
plug-ins instead of forking it.

## Concepts

| Term | Meaning |
|------|---------|
| Platform | The governed core every product shares: schemas `Meta`, `RBAC`, `portal`, `wf`, `cfg`, `Contract`, `Onboarding`, `inv` |
| Descendant application | A product built on the platform. It adds classes, actions, semantic entities and navigation as data; it never edits the platform |
| Standalone utility | A tool that talks to the platform over published APIs only |
| Database-governed | Behavior, permissions, navigation and history are rows you can version, review and query |

Why enterprises care: many products share one security and compliance surface; customizing a product does
not create a fork; and because behavior is data, it can be audited.

## In GoliathApp

* `README.md`, [`docs/architecture.md`](https://github.com/Goliath-Research/GoliathApp/blob/main/docs/architecture.md), `docs/platform.md`, `docs/feature-catalog.md`.
* The dependency rule is enforced by tests: `workflow_engine/tests/test_goliathapp_no_child_app_tokens.py`
  and `test_platform_decoupling.py` reject any reference from the platform to a product.
* Only **God Architect** may change `platform/*` definitions (Module 8).

## Lab sequence

1. Read `docs/architecture.md` and draw the platform / descendant / standalone boundary for `acme_child`,
   the fictional bench-instrument company used throughout this course.
2. Open `test_goliathapp_no_child_app_tokens.py` and explain in two sentences what it would reject.
3. Classify these ten capabilities as platform, descendant or standalone: sign-in, organization
   membership, instrument calibration schedule, workflow engine, worker client, calibration certificate
   layout, audit ledgers, electronic signatures, a CSV export script, the acme_child menu entries.

## Evidence to submit

A one-page boundary diagram and the classification table with one sentence of reasoning per row.

## Handoff to Module 2

Module 2 installs the platform you just described, exactly as a release would.
