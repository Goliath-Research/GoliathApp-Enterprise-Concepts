# Module 4: Meta Object Model II

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

See a class as a published **contract**: a generated JSON Schema, validation at more than one layer, and
versioned changes.

## Concepts

* Every class publishes a JSON Schema (`"Meta".fn_class_json_schema(class_id)`) and a catalog type in
  `wf.data_type` (`meta/class/<name>`).
* Validation layers: an always-on unknown/required key check in PostgreSQL, optional `pg_jsonschema`,
  and Pydantic models on the Python side.
* Changes follow MAJOR.MINOR rules: adding a required property is breaking; tightening is minor
  (`docs/meta-model.md`, decision D6).

## Lab sequence

1. `SELECT "Meta".fn_class_json_schema(<Instrument class id>);` and find `SerialNumber` under `required`.
2. As the operator, insert an instrument with an unknown key (`"Colour"`). It is rejected.
3. Insert one without `SerialNumber`. It is rejected.
4. Find the published catalog type: `SELECT name, version FROM wf.data_type WHERE name = 'meta/class/acme_child/Instrument' ORDER BY version;`
   Expect versions `1.0` to `1.4`: creating the class published `1.0`, and each of its four fields
   published a new minor version. Re-running setup publishes nothing new.

## Evidence to submit

`pytest "4 - Meta Object Model II"` output and the two rejection messages.

## Handoff to Module 5

Data has contracts; Module 5 gives behavior the same treatment.
