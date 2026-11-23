# Module 11: Events & Device Adapters

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Ingest events idempotently and let subscriptions start or signal workflows; understand why an adapter's
acknowledgement is not proof that something physically happened.

## Concepts

* An event is a fact with an identity: `source` + `idempotency_key` (`wf.sp_ingest_event`).
* Ingesting the same identity twice returns `duplicate = true` and changes nothing.
* Subscriptions start or signal workflows; deliveries are recorded in `wf.event_delivery`.
* Since GoliathApp PR #109, `wf.event` and `wf.event_delivery` are hash-chained ledgers.

## Lab sequence

1. Ingest a `course.lab.reading` event from source `acme_child-bench (course lab)` with a key of your choice.
2. Ingest it again with the same key and read `duplicate`.
3. `SELECT * FROM portal.fn_ledger_verify('wf.event');` returns no rows.

## Evidence to submit

`pytest "11 - Events & Device Adapters"` output.

## Handoff to Module 12

Module 12 configures the site that produces these events.
