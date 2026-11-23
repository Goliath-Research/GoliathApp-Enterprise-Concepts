import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium", app_title="Module 8: Authorization, Tenancy & Navigation")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        """
        # Module 8: Authorization, Tenancy & Navigation

        *GoliathApp: Enterprise Application Concepts · Goliath Research Academy*

        Choose a course user, a role and an object. The notebook opens a real session (as the portal
        does) and tries to read the object, then shows the user's grants and menu entries.
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
        objs = {f"{d['Label']} (#{i})": i for i, d in _conn.execute(
            """SELECT o."ID", "Meta".fn_merged_obj_document(o."ID") FROM "Meta"."Objs" o
               JOIN "Meta"."Classes" c ON c."ID" = o."ClassID" WHERE c."Name" = 'acme_child/Instrument'"""
        ).fetchall()}
    who = mo.ui.dropdown({"Oscar Operator (AcmeChild)": ("operator", "scope_a"),
                          "Olivia Outsider (Bench Partners)": ("outsider", "scope_b"),
                          "Ada Admin (AcmeChild)": ("admin", "scope_a")},
                         value="Oscar Operator (AcmeChild)", label="User")
    role = mo.ui.dropdown(["acme_child_operator", "organization_admin", "god_architect"],
                          value="acme_child_operator", label="Active role")
    obj = mo.ui.dropdown(objs, value=next(iter(objs)), label="Instrument")
    mo.vstack([who, role, obj])
    return cs, obj, role, who


@app.cell
def _(cs, mo, obj, role, who):
    user_key, scope_key = who.value
    try:
        _token = cs.open_session(user_key, scope_key=scope_key, role=role.value)
        with cs.portal() as _conn:
            rows = _conn.execute("SELECT document FROM portal.sp_session_meta_obj_get(%s, %s)", (_token, obj.value)).fetchall()
        verdict = mo.callout(mo.md(f"**Allowed.** `{rows[0][0]}`" if rows else "**Not visible** (no rows)."),
                             kind="success" if rows else "danger")
    except Exception as exc:  # noqa: BLE001 - show the platform's refusal as-is
        verdict = mo.callout(mo.md(f"**Refused:** `{type(exc).__name__}: {str(exc).splitlines()[0]}`"), kind="danger")
    with cs.owner() as _conn:
        grants = _conn.execute(
            """SELECT r."Name", g."GrantType", g."ScopeID" FROM "RBAC"."UserRoleGrants" g
               JOIN "RBAC"."Roles" r ON r."ID" = g."RoleID"
               WHERE g."UserID" = %s AND g."Active" ORDER BY 1""", (cs.lab_ids()[user_key],)
        ).fetchall()
    mo.vstack([verdict, mo.md("### Role grants"), mo.ui.table([{"role": r, "grant": t, "scope": sc} for r, t, sc in grants])])
    return


if __name__ == "__main__":
    app.run()
