# Module 2: Reproducible Installation

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Treat the database as a release artifact: ordered, re-runnable DDL; data populated in layers; one database
role per process with only the rights it needs.

## Run

```bash
cp .env.example .env
python course_lab.py up        # postgres:19-bookworm on 127.0.0.1 only
python course_lab.py setup     # official apply + seeds, then course data
```

`lab/setup_lab.py` follows GoliathApp's documented population order
([`docs/database-population.md`](https://github.com/Goliath-Research/GoliathApp/blob/main/docs/database-population.md)):

| Layer | Official script | What it adds |
|-------|-----------------|--------------|
| 1. Schema | `workflow_engine/sql_pg/apply_schema.sh` | Every schema, function and trigger, in a fixed order, with `ON_ERROR_STOP`, then a contract check |
| 2. Platform seeds | `seed_semantic_catalog.py`, `seed_action_catalog.py --use-db`, `seed_platform_nav_tree.sql` | Semantic registry, action catalog, platform menu |
| 3. Tenant bootstrap | platform functions (`portal.sp_organization_create`, `sp_upsert_user`, `sp_grant_user_role`) | Two course organizations and three course users |
| 4. Descendant rows | portal session API | The `acme_child` classes and instruments |

Layers 3 and 4 are **course lab data**: every name says "(course lab)" and every email uses the reserved
`.invalid` domain. The script refuses any database host that is not local.

## Lab sequence

1. Run `python course_lab.py setup` twice. The second run changes nothing: apply is idempotent and the
   course data steps check before they insert.
2. `python course_lab.py psql` and run `SELECT count(*) FROM wf.workflow_action;` (14 platform actions)
   and `SELECT count(*) FROM portal."NavTree";` (the platform menu).
3. Least privilege: connect as `goliath_portal` (the role the portal uses) and try
   `SELECT * FROM "RBAC"."Users";`. It fails with *permission denied*. The same role can call
   `portal.*` functions, which check the session themselves.

## Evidence to submit

`pytest "2 - Reproducible Installation"` output, and a short note explaining why the portal role has no
table access at all.

## Handoff to Module 3

The schema is installed; Module 3 models the `acme_child` domain in it.
