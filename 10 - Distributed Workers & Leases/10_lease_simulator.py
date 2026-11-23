import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium", app_title="Module 10: Distributed Workers & Leases")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        """
        # Module 10: Distributed Workers & Leases

        *GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

        Workers claim tasks and hold **time-limited leases**. A crashed worker stops sending heartbeats,
        its lease expires, and reclaim puts the task back in the queue. Move the sliders and watch every
        task still finish, with no task ever held by two live leases.
        """
    )
    return (mo,)


@app.cell
def _(mo):
    tasks = mo.ui.slider(5, 80, value=30, label="Tasks")
    workers = mo.ui.slider(1, 10, value=4, label="Workers")
    lease = mo.ui.slider(2, 30, value=10, label="Lease seconds")
    crash = mo.ui.slider(0.0, 0.8, step=0.05, value=0.25, label="Crash rate")
    mo.vstack([tasks, workers, lease, crash])
    return crash, lease, tasks, workers


@app.cell
def _(crash, lease, mo, tasks, workers):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from module_10_support import simulate

    r = simulate(tasks=tasks.value, workers=workers.value, lease_seconds=lease.value, crash_rate=crash.value, seed=7)
    mo.md(
        f"""
        | Measure | Value |
        |---|---|
        | Tasks completed | {r.completed} of {tasks.value} |
        | Claims (attempts) | {r.attempts} |
        | Leases reclaimed after a crash | {r.reclaimed} |
        | Most live leases on one task at once | {r.max_concurrent_holders_per_task} |
        """
    )
    return (r,)


@app.cell
def _(mo, r):
    rows = [{"t": t, "event": e, "task": k, "worker": w} for t, e, k, w in r.timeline[:200]]
    mo.ui.table(rows, label="First 200 events")
    return


if __name__ == "__main__":
    app.run()
