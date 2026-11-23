"""A small discrete-time model of GoliathApp's leased work (Module 10). No database needed.

Rules modelled after wf.task_lease and the worker protocol:
* a worker claims a READY task and gets a lease that ends at now + lease_seconds;
* a live worker finishes its task after `work_seconds` (heartbeats keep the lease alive meanwhile);
* a worker may crash; its lease is not renewed and expires;
* reclaim returns tasks with expired leases to READY; a restarted worker claims again.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Lease:
    task: int
    worker: int
    expires_at: int
    finishes_at: int
    crashed: bool


@dataclass
class SimResult:
    completed: int = 0
    reclaimed: int = 0
    attempts: int = 0
    max_concurrent_holders_per_task: int = 0
    timeline: list[tuple[int, str, int, int]] = field(default_factory=list)  # (t, event, task, worker)


def simulate(*, tasks: int = 20, workers: int = 3, lease_seconds: int = 10, work_seconds: int = 4,
             crash_rate: float = 0.2, seed: int = 1, max_time: int = 10_000) -> SimResult:
    rng = random.Random(seed)
    ready = list(range(tasks))
    leases: dict[int, Lease] = {}  # worker -> lease
    done: set[int] = set()
    res = SimResult()
    t = 0
    while len(done) < tasks and t < max_time:
        # reclaim expired leases (crashed workers stop heartbeating)
        for w, lease in list(leases.items()):
            if lease.crashed and lease.expires_at <= t:
                del leases[w]
                ready.append(lease.task)
                res.reclaimed += 1
                res.timeline.append((t, "reclaim", lease.task, w))
        # finish work for live workers
        for w, lease in list(leases.items()):
            if not lease.crashed and lease.finishes_at <= t:
                del leases[w]
                done.add(lease.task)
                res.completed += 1
                res.timeline.append((t, "submit", lease.task, w))
        # idle workers claim
        for w in range(workers):
            if w not in leases and ready:
                task = ready.pop(0)
                crashed = rng.random() < crash_rate
                leases[w] = Lease(task, w, t + lease_seconds, t + work_seconds, crashed)
                res.attempts += 1
                res.timeline.append((t, "claim", task, w))
                if crashed:
                    res.timeline.append((t + 1, "crash", task, w))
        holders: dict[int, int] = {}
        for lease in leases.values():
            holders[lease.task] = holders.get(lease.task, 0) + 1
        res.max_concurrent_holders_per_task = max([res.max_concurrent_holders_per_task, *holders.values()])
        t += 1
    return res
