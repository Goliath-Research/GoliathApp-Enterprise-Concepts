import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium", app_title="Module 13: Traceability & Audit")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        """
        # Module 13: Traceability & Audit

        *GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

        Pick an instrument: read **who changed what and when**, see the record **as of** any moment,
        list its **electronic signatures**, and verify every history ledger. Requires GoliathApp with
        the history PR stack (#109–#112), as pinned in `lab/GOLIATHAPP_PIN`.
        """
    )
    return (mo,)


@app.cell
def _(mo):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import course_support as cs

    ok, reason = cs.lab_ready()
    mo.stop(not ok, mo.callout(mo.md(f"**Lab not ready:** {reason}"), kind="warn"))
    with cs.owner() as _conn:
        mo.stop(not cs.has_function(_conn, "portal.sp_session_sign(text,text,text,text,text)"),
                mo.callout(mo.md("This lab runs a GoliathApp without the history features (PRs #109–#112)."), kind="warn"))
        objs = {f"{d.get('Label')} (#{i})": i for i, d in _conn.execute(
            """SELECT o."ID", "Meta".fn_merged_obj_document(o."ID") FROM "Meta"."Objs" o
               JOIN "Meta"."Classes" c ON c."ID" = o."ClassID" WHERE c."Name" = 'acme_child/Instrument'
               ORDER BY o."ID" """
        ).fetchall()}
    obj = mo.ui.dropdown(objs, value=next(iter(objs)), label="Instrument")
    obj
    return cs, obj


@app.cell
def _(cs, mo, obj):
    _token = cs.open_session("operator", role="acme_child_operator")
    with cs.portal() as _conn:
        hist = _conn.execute(
            """SELECT changed_at_utc, change_kind, level_class_name, actor_email, data_before, data_after
               FROM portal.sp_session_meta_obj_history(%s, %s)""", (_token, obj.value)
        ).fetchall()
        sigs = _conn.execute(
            "SELECT signer_full_name, meaning_label, signed_at_utc, status, comment FROM portal.sp_session_signatures(%s, 'meta.object', %s)",
            (_token, str(obj.value)),
        ).fetchall()
    times = list(dict.fromkeys(str(h[0]) for h in hist))
    when = mo.ui.dropdown(times, value=times[0] if times else None, label="Show the record as of")
    mo.vstack([
        mo.md(f"### History ({len(hist)} changes)"),
        mo.ui.table([{"at (UTC)": str(h[0]), "change": h[1], "level": h[2], "by": h[3], "before": h[4], "after": h[5]}
                     for h in hist]),
        mo.md(f"### Signatures ({len(sigs)})"),
        mo.ui.table([{"signer": s[0], "meaning": s[1], "at": s[2], "status": s[3], "comment": s[4]} for s in sigs]),
        when,
    ])
    return (when,)


@app.cell
def _(cs, mo, obj, when):
    mo.stop(when.value is None)
    with cs.owner() as _conn:
        _doc = _conn.execute('SELECT "Meta".fn_merged_obj_document_as_of(%s, %s::timestamptz)', (obj.value, when.value)).fetchone()[0]
        _problems = _conn.execute("SELECT * FROM portal.fn_ledger_verify_all()").fetchall()
    mo.vstack([
        mo.md(f"### As of {when.value}"), mo.json(_doc or {}),
        mo.callout(mo.md("**All history ledgers verify.**" if not _problems else f"**Ledger _problems:** {_problems}"),
                   kind="success" if not _problems else "danger"),
    ])
    return


if __name__ == "__main__":
    app.run()
