# Module 3: Meta Object Model I

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Model a domain as **data**: classes with single inheritance, fields, objects and links, without creating
tables or redeploying.

## Concepts

An *adaptive object model* stores classes and fields as rows. GoliathApp's `Meta` schema holds:

| Table | Holds |
|-------|-------|
| `"Meta"."Classes"` | Class name, `ParentID` (single inheritance), abstract flag |
| `"Meta"."ClassClosure"` | Every ancestor/descendant pair, for polymorphic queries |
| `"Meta"."Fields"` | Typed fields; each field is declared on exactly one class level |
| `"Meta"."Objs"` | One row per object, with its concrete class |
| `"Meta"."ObjValues"` | One JSONB document **per inheritance level** of an object |
| `"Meta"."Links"` | Class-level link definitions and instance links |

The generic hierarchy (`platform/Entity`, `Party`, `Organization`, `Person`, `Item`, `Batch`, ...) comes
from the platform; products hang their classes under it.

## In the lab

`lab/setup_lab.py` created, through the portal session API as the organization admin:

* `acme_child/Instrument` under `platform/Item`: Label, SerialNumber, Model, CalibrationIntervalDays
* `acme_child/CalibrationRun` under `platform/Batch`: Label, InstrumentSerial, PerformedOn, Result, DeviationPercent

## Lab sequence

1. Open the notebook: `marimo edit "3 - Meta Object Model I/03_meta_hierarchy_explorer.py"`.
2. Pick `acme_child/Instrument` and read its lineage up to `platform/Entity` from `ClassClosure`.
3. Read its resolved fields from `"Meta"."VClassFieldsResolved"` and the per-level `ObjValues` rows of an
   instrument.
4. Polymorphism: list every object whose class descends from `platform/Item`. The instruments appear
   without any query naming `acme_child`.

## Practice

Add a `acme_child/Reading` class under `platform/Observation` with `portal.sp_session_meta_class_create`
and `portal.sp_session_meta_field_upsert`, using an admin session (see `course_support.open_session`).

## Evidence to submit

`pytest "3 - Meta Object Model I"` output and a screenshot of the explorer showing the lineage.

## Handoff to Module 4

Classes are contracts. Module 4 shows how GoliathApp validates documents against them.
