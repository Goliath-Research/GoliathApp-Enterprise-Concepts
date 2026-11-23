# Module 8: Authorization, Tenancy & Navigation

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Explain every access decision: roles and permissions, organizations as tenants, layered class and object
rules, navigation as an entitlement, and **God Architect** ownership of `platform/*`.

## Concepts

* RBAC: users, roles, permissions; grants are **scoped** to an organization's scope.
* Multi-tenancy: objects are scoped (`portal."ScopedMetaObjects"`); sessions have one active scope.
* Layered decisions: object rule, then class rule, then permission (`docs/platform-layered-security.md`).
* Navigation is an entitlement (`portal."NavTree"`, `Role2Node`).
* Model authority: only the `god_architect` role may create or change `platform/*` classes and objects;
  organization admins author their own namespaces (`acme_child/*`). Class and field changes are
  audited in `portal.model_authoring_audit`; every role switch (including into God Architect) in
  `portal.session_active_role_audit`; and, with GoliathApp PR #110, every object change in
  `"Meta"."ObjValuesHistory"` with the acting user (Module 13).

## Lab sequence

1. Open the notebook `08_permission_explainer.py` and pick each course user against
   `acme_child/Instrument`.
2. As the outsider (Bench Partners), try to read one of AcmeChild's instruments with
   `portal.sp_session_meta_obj_get`. It fails with SQLSTATE `GS404` *meta object not found*: another
   tenant's record is reported as missing, so its existence is not revealed.
3. As the operator, try to create a `platform/RetentionPolicy` object. It is refused: platform classes
   belong to God Architect.
4. As the course admin with the `god_architect` role active, creating a `platform/SignatureMeaning`
   succeeds (lab only; the label says "(course lab)"). Find the role switch in
   `portal.session_active_role_audit` and the new object, attributed to the admin, in
   `"Meta"."ObjValuesHistory"`.

## Evidence to submit

`pytest "8 - Authorization, Tenancy & Navigation"` output and a 3x3 access matrix (users x actions) with
the rule that decided each cell.

## Handoff to Module 9

Permissions protect data and work. Module 9 defines the work.
