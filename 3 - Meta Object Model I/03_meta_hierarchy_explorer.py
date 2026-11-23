import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium", app_title="Module 3: Meta Object Model I")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        """
        # Module 3: Meta Object Model I

        *GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

        Pick a class to see its lineage (single inheritance up to `platform/Entity`), its resolved fields,
        and its objects. Everything here is rows in the `Meta` schema of your local course lab.
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
        names = [r[0] for r in _conn.execute('SELECT "Name" FROM "Meta"."Classes" ORDER BY "Name"').fetchall()]
    picker = mo.ui.dropdown(names, value="acme_child/Instrument", label="Class")
    picker
    return cs, picker


@app.cell
def _(cs, mo, picker):
    with cs.owner() as _conn:
        cid = cs.class_id(_conn, picker.value)
        lineage = _conn.execute(
            """SELECT a."Name", cc."Depth" FROM "Meta"."ClassClosure" cc
               JOIN "Meta"."Classes" a ON a."ID" = cc."AncestorID"
               WHERE cc."DescendantID" = %s ORDER BY cc."Depth" """, (cid,)
        ).fetchall()
        fields = _conn.execute(
            'SELECT * FROM "Meta"."VClassFieldsResolved" WHERE "ClassID" = %s', (cid,)
        ).fetchall()
        objs = _conn.execute(
            """SELECT o."ID", "Meta".fn_merged_obj_document(o."ID") FROM "Meta"."Objs" o
               WHERE o."ClassID" = %s ORDER BY o."ID" LIMIT 50""", (cid,)
        ).fetchall()
    mo.vstack([
        mo.md("### Lineage (depth 0 is the class itself)"),
        mo.ui.table([{"class": n, "depth": d} for n, d in lineage]),
        mo.md(f"### Resolved fields ({len(fields)})"),
        mo.ui.table([dict(enumerate(map(str, f))) for f in fields]),
        mo.md(f"### Objects ({len(objs)})"),
        mo.ui.table([{"id": i, "document": d} for i, d in objs]),
    ])
    return


if __name__ == "__main__":
    app.run()
