# Module 7: Authentication & Sessions

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Separate **authentication** (who you are, delegated to an identity provider) from the application's own
server-side **sessions**.

## Concepts

* The portal signs users in with OIDC (authorization code + PKCE) and links the provider subject to a
  local user (`"RBAC"."ExternalIdentities"`); it never links on an unverified email alone.
* `portal.sp_session_open` creates a session; the browser holds an opaque token, and the database stores
  only its SHA-256 (`"RBAC"."SessionTokens"."TokenHash"`), with idle and absolute timeouts.
* One active role per session; every change is audited in `portal.session_active_role_audit`.
* `"RBAC"."Sessions"."AuthenticatedAtUtc"` records when the user last proved who they are; electronic
  signatures (Module 13) require it to be recent.

**Safety.** This course signs in through the portal's integration-only dev login, enabled only on your
local lab with a local secret. It must never be enabled on a shared or production portal.

## Lab sequence

1. Open a session with `course_support.open_session("operator")` and resolve it with
   `portal.fn_session_resolve(token)`.
2. Show that the token itself appears nowhere in `"RBAC"."SessionTokens"`; only its hash does.
3. Read `portal.session_active_role_audit` for that session.

## Evidence to submit

`pytest "7 - Authentication & Sessions"` output.

## Handoff to Module 8

A session says who you are. Module 8 decides what you may do.
