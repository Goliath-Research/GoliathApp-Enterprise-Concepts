# Module 14: Descendant Applications & Capstone

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Plan and prove a descendant application: everything `acme_child` needs is data on top of an untouched
platform, and it can be rebuilt from scratch.

## Capstone

1. Reset the lab: `python course_lab.py reset && python course_lab.py up && python course_lab.py setup`.
2. Re-create your Module 3 practice class and Module 13 meanings on the fresh database.
3. Run the whole course suite: `pytest`. Every module test passes or skips with a stated reason.
4. Run the portal against the lab (README section 5.3) and `pytest tests/test_portal_lab.py`.
5. Write `RUNBOOK.md` for a colleague, and a one-page "platform vs product" boundary statement.

## Evidence to submit

* Full `pytest` output on a fresh lab, including the portal tests.
* `RUNBOOK.md` and the boundary statement.
* `SELECT * FROM portal.fn_ledger_checkpoint();` output, kept as your off-database checkpoint.
