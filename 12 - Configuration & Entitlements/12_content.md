# Module 12: Configuration & Entitlements

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Use typed, versioned configuration documents with draft and published states and content hashes; keep
secrets as references, never in documents.

## Concepts

* `cfg.cfg_repo_upsert(kind, name, version, status, document)` stores a typed document; `cfg_repo_get`
  reads it with its `content_hash`; `cfg_repo_publish` makes a version official.
* Callers can ask for published versions only, so drafts never leak into runs.
* Entitlements (what a role may open) are navigation grants, managed like any other data (Module 8).

## Lab sequence

1. Upsert a draft `site` document named `acme-child-bench (course lab)` version `1`.
2. Read it with `published_only => true` (nothing) and `false` (the draft).
3. Publish it and read it again. Note the `content_hash`.

## Evidence to submit

`pytest "12 - Configuration & Entitlements"` output.

## Handoff to Module 13

Every change you have made so far left a trace. Module 13 reads it.
