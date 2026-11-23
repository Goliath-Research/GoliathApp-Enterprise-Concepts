# Module 13: Traceability & Audit

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Reconstruct *who did what, when, with which content*, prove that nothing was changed or removed, and sign
records electronically.

> **Status.** The history features taught here were merged into GoliathApp `main` as pull requests
> **#109–#112**, followed by **#113** (every timestamp stored as UTC). The lab pins GoliathApp to that
> commit (`lab/GOLIATHAPP_PIN`). Tests skip with a clear message if your lab runs an older GoliathApp.

## Concepts

| Feature (GoliathApp PR) | What it gives you |
|-------------------------|-------------------|
| Ledgers (#109) | Every audit table and the event plane is **append-only** and **hash-chained**: `row_hash = sha256(prev_hash || row)`. `portal.fn_ledger_verify_all()` reports any edit (`hash_mismatch`) or removal (`missing_seq`). `portal.fn_ledger_checkpoint()` is exported off-database to detect even an owner rewriting the chain |
| Meta object history (#110) | `"Meta"."ObjValuesHistory"` records every object, value, link and scope change for **every class**, with the session user. `"Meta".fn_merged_obj_document_as_of(obj, time)` shows a record as it was |
| Run history and retention (#111) | `wf.run_history` keeps run transitions and worker leases. Runs cannot be deleted; `platform/RetentionPolicy.PurgeExpiredRuns` removes them only after `RetentionDays`, never under `LegalHold`, leaving tombstones and a `run.purge` record |
| Electronic signatures (#112) | `portal.sp_session_sign` binds signer, meaning, time and a SHA-256 of the record's content; requires a recent sign-in; `content_changed` shows a record edited after signing; signed records cannot be deleted or purged |
| UTC timestamps (#113) | Every `*_at_utc` column is a `timestamptz` written with `now()`, so history times are true UTC instants from any session time zone (ALCOA+ *contemporaneous*). `portal.fn_utc_timestamp_violations()` is empty on a correct install |

These map to the ALCOA+ expectations for regulated records (attributable, legible, contemporaneous,
original, accurate; complete, consistent, enduring, available).

## Lab sequence

1. Open `13_evidence_trail.py`. Pick an instrument and read its history: who created it, every edit,
   from which session.
2. Edit the instrument as the operator (in the portal or with `portal.sp_session_meta_obj_update`), then
   read it *as of* a minute ago.
3. As God Architect, create a signature meaning `Reviewed (course lab)`; as the operator, sign the
   instrument; edit it; list signatures and see `content_changed`.
4. Try to delete the signed instrument as the database owner. It is refused.
5. `SELECT * FROM portal.fn_ledger_verify_all();` returns no rows.

## Evidence to submit

`pytest "13 - Traceability & Audit"` output and a one-page ALCOA+ table: for each letter, the GoliathApp
feature that provides it and anything still missing (for example the portal signing screen, a follow-up).

## Handoff to Module 14

Module 14 rebuilds everything on a fresh database and proves it end to end.
