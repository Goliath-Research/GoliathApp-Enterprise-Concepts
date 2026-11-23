# Module 10: Distributed Workers & Leases

*GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

[Back to the syllabus](../README.md)

## Goal

Understand **leased** work: a worker claims a task, holds a time-limited lease, sends heartbeats and
submits or fails; expired leases return to the queue. Workers never connect to the database.

## Concepts

* Workers talk only to `goliath-gateway` over HTTP (`contracts/openapi.yaml`, `workers/WORKER_PROTOCOL.md`).
* `wf.task_lease` holds the current lease only; reclaim returns expired leases to READY.
* Wake hints (`POST /v1/workers/wakes/wait`) reduce latency but never grant ownership; claiming does.
* With GoliathApp PR #111, every lease acquire, transfer and release is also written to the
  `wf.run_history` ledger, so you can tell later which worker held a task even though the lease row is gone.

## Lab sequence

1. Open `10_lease_simulator.py`: workers, leases, heartbeats and crashes on a time axis. Change lease
   length and failure rate and watch reclaim keep every task done exactly once per successful attempt.
2. In the database, take the READY task from Module 9 and trace what a worker would do through the gateway.
3. Optional, advanced: run the gateway and the `goliath_worker` client from `.lab/GoliathApp`
   (`docs/workers.md`). This is not run by the course tests.

## Evidence to submit

`pytest "10 - Distributed Workers & Leases"` output and a paragraph: why is a wake hint not a lease?

## Handoff to Module 11

Work can also start from the outside world. Module 11 ingests events.
