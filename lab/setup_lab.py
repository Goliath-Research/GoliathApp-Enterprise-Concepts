"""Build the course lab database from GoliathApp's official scripts, then add course data.

Steps (each is the official GoliathApp path; see GoliathApp docs/database-population.md):

1. Check out GoliathApp at the commit pinned in lab/GOLIATHAPP_PIN (or use GOLIATHAPP_SRC).
2. workflow_engine/sql_pg/apply_schema.sh                 schema, ordered and re-runnable
3. workflow_engine/sql_pg/seed_semantic_catalog.py        platform semantic registry
4. workflow_engine/sql_pg/seed_action_catalog.py --use-db platform action catalog
5. Course organizations, users and roles (lab/course_data.py) through platform functions
6. workflow_engine/sql_pg/seed_platform_nav_tree.sql      platform menu (after scopes exist)
7. acme_child classes and objects through the portal session API
8. goliath_portal login for the local portal; .lab/lab.env with the ids tests and the portal use

Safety: the target must be a loopback or Compose-internal host. This script refuses anything else,
so it can never touch a shared or production database.

Usage:
    python lab/setup_lab.py            # uses PG* variables (see .env.example)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab import course_data as data  # noqa: E402

LAB_DIR = ROOT / ".lab"
PIN_FILE = ROOT / "lab" / "GOLIATHAPP_PIN"
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "db", "postgres"}


def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def read_pin() -> dict[str, str]:
    pin: dict[str, str] = {}
    for line in PIN_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            pin[key.strip()] = value.strip()
    return pin


def pg_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PGHOST", "127.0.0.1")
    env.setdefault("PGPORT", env.get("PG_HOST_PORT", "54339"))
    env.setdefault("PGUSER", env.get("POSTGRES_USER", "postgres"))
    env.setdefault("PGDATABASE", env.get("POSTGRES_DB", "goliathapp_lab"))
    if "PGPASSWORD" not in env and "POSTGRES_PASSWORD" in env:
        env["PGPASSWORD"] = env["POSTGRES_PASSWORD"]
    if env["PGHOST"] not in ALLOWED_HOSTS:
        raise SystemExit(
            f"Refusing to set up a lab on PGHOST={env['PGHOST']!r}: the course lab only runs on a "
            "local disposable database (127.0.0.1, localhost or the Compose service)."
        )
    # apply_schema.sh and the GoliathApp tests read POSTGRES_*.
    env["POSTGRES_HOST"] = env["PGHOST"]
    env["POSTGRES_PORT"] = env["PGPORT"]
    env["POSTGRES_USER"] = env["PGUSER"]
    env["POSTGRES_DB"] = env["PGDATABASE"]
    env["POSTGRES_PASSWORD"] = env.get("PGPASSWORD", "")
    return env


def goliathapp_checkout() -> Path:
    src = os.environ.get("GOLIATHAPP_SRC")
    if src:
        return Path(src).resolve()
    pin = read_pin()
    target = LAB_DIR / "GoliathApp"
    if not (target / ".git").exists():
        LAB_DIR.mkdir(exist_ok=True)
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "remote", "add", "origin", pin["repository"]], check=True)
    subprocess.run(["git", "-C", str(target), "fetch", "-q", "--depth", "1", "origin", pin["commit"]], check=True)
    subprocess.run(["git", "-C", str(target), "checkout", "-q", "--detach", pin["commit"]], check=True)
    return target


def ensure_engine_packages(app: Path, env: dict[str, str]) -> None:
    """The official seed scripts import GoliathApp's Python packages; install them once into this venv."""
    probe = subprocess.run([sys.executable, "-c", "import pydantic, psycopg"], env=env, capture_output=True)
    if probe.returncode != 0:
        run([sys.executable, "-m", "pip", "install", "-q", "-e", str(app / "workflow_engine")], env)


def run(cmd: list[str], env: dict[str, str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, env=env, cwd=cwd, check=True)


def conninfo(env: dict[str, str]) -> str:
    return (
        f"host={env['PGHOST']} port={env['PGPORT']} dbname={env['PGDATABASE']} "
        f"user={env['PGUSER']} password={env.get('PGPASSWORD', '')}"
    )


def scalar(conn: psycopg.Connection, sql: Any, params: tuple[Any, ...] = ()) -> Any:
    row = conn.execute(sql, params).fetchone()
    return None if row is None else row[0]


def ensure_org(conn: psycopg.Connection, name: str) -> tuple[int, int]:
    row = conn.execute(
        """SELECT o."ID", s."ScopeID" FROM portal."Organizations" o
           JOIN "RBAC"."Scopes" s ON s."OrganizationID" = o."ID"
           WHERE o."Name" = %s ORDER BY s."ScopeID" LIMIT 1""",
        (name,),
    ).fetchone()
    if row is None:
        row = conn.execute("SELECT * FROM portal.sp_organization_create(%s)", (name,)).fetchone()
    assert row is not None
    return int(row[0]), int(row[1])


def ensure_operator_role(conn: psycopg.Connection) -> int:
    role_id = scalar(conn, 'SELECT "ID" FROM "RBAC"."Roles" WHERE "Name" = %s', (data.OPERATOR_ROLE,))
    if role_id is None:
        role_id = scalar(conn, "SELECT portal.sp_create_role(%s, false)", (data.OPERATOR_ROLE,))
    for perm in data.OPERATOR_PERMISSIONS:
        conn.execute("SELECT portal.sp_set_role_permission(%s, %s, true)", (role_id, perm))
    return int(role_id)


def grant_nav(conn: psycopg.Connection, role_id: int, scope_id: int) -> None:
    for (node_id,) in conn.execute(
        """SELECT n."ID" FROM portal."NavTree" n WHERE n."NodePath" LIKE '/app%%'"""
    ).fetchall():
        conn.execute("SELECT portal.sp_grant_role_nav_node(%s, %s, %s)", (role_id, node_id, scope_id))


def bootstrap_people(conn: psycopg.Connection) -> dict[str, int]:
    ids: dict[str, int] = {}
    org_a, scope_a = ensure_org(conn, data.ORG_A)
    org_b, scope_b = ensure_org(conn, data.ORG_B)
    ids.update(org_a=org_a, scope_a=scope_a, org_b=org_b, scope_b=scope_b)
    for user in data.USERS:
        ids[user.key] = int(scalar(conn, "SELECT user_id FROM portal.sp_upsert_user(%s, %s, 1)", (user.email, user.full_name)))
    conn.execute("SELECT portal.sp_organization_set_admin(%s, %s)", (org_a, ids["admin"]))
    # Lab only: the course admin also holds God Architect so Modules 8 and 13 can show platform ownership.
    conn.execute("SELECT portal.sp_security_meta_grant_god_architect_to_user(%s)", (ids["admin"],))
    role_id = ensure_operator_role(conn)
    ids["operator_role"] = role_id
    for key, scope in (("operator", scope_a), ("outsider", scope_b)):
        conn.execute("SELECT * FROM portal.sp_grant_user_role(%s, %s, 'SCOPED', %s)", (ids[key], role_id, scope))
    return ids


def open_session(conn: psycopg.Connection, user_id: int, scope_id: int, role_name: str) -> str:
    token = str(scalar(conn, "SELECT session_token FROM portal.sp_session_open(%s, %s)", (user_id, scope_id)))
    role_id = scalar(conn, 'SELECT "ID" FROM "RBAC"."Roles" WHERE "Name" = %s', (role_name,))
    conn.execute("SELECT * FROM portal.sp_session_set_active_role(%s, %s)", (token, role_id))
    return token


def bootstrap_model(conn: psycopg.Connection, ids: dict[str, int]) -> None:
    admin = open_session(conn, ids["admin"], ids["scope_a"], "organization_admin")
    for class_name, parent, fields in data.CLASSES:
        if scalar(conn, 'SELECT 1 FROM "Meta"."Classes" WHERE "Name" = %s', (class_name,)) is None:
            conn.execute("SELECT * FROM portal.sp_session_meta_class_create(%s, %s, %s)", (admin, class_name, parent))
        for field, type_name, required in fields:
            conn.execute(
                "SELECT * FROM portal.sp_session_meta_field_upsert(%s, %s, %s, %s, '1.0', %s)",
                (admin, class_name, field, type_name, required),
            )
    conn.execute("SELECT portal.sp_nav_ensure_meta_catalog()")


def bootstrap_objects(conn: psycopg.Connection, ids: dict[str, int]) -> None:
    from psycopg.types.json import Jsonb

    for key, scope, docs in (
        ("operator", ids["scope_a"], data.INSTRUMENTS),
        ("outsider", ids["scope_b"], data.OUTSIDER_INSTRUMENTS),
    ):
        token = open_session(conn, ids[key], scope, data.OPERATOR_ROLE)
        for doc in docs:
            exists = scalar(
                conn,
                """SELECT 1 FROM "Meta"."ObjValues" v JOIN "Meta"."Classes" c ON c."ID" = v."ClassID"
                   WHERE c."Name" = 'acme_child/Instrument' AND v."Data" ->> 'SerialNumber' = %s""",
                (doc["SerialNumber"],),
            )
            if exists is None:
                conn.execute(
                    "SELECT portal.sp_session_meta_obj_insert(%s, 'acme_child/Instrument', %s)", (token, Jsonb(doc))
                )


def write_lab_env(env: dict[str, str], ids: dict[str, int]) -> None:
    LAB_DIR.mkdir(exist_ok=True)
    lines = [
        "# Generated by lab/setup_lab.py for the local course lab. Do not commit.",
        f"COURSE_ORG_A_ID={ids['org_a']}",
        f"COURSE_SCOPE_A_ID={ids['scope_a']}",
        f"COURSE_ORG_B_ID={ids['org_b']}",
        f"COURSE_SCOPE_B_ID={ids['scope_b']}",
        f"COURSE_ADMIN_USER_ID={ids['admin']}",
        f"COURSE_OPERATOR_USER_ID={ids['operator']}",
        f"COURSE_OUTSIDER_USER_ID={ids['outsider']}",
        f"COURSE_OPERATOR_ROLE_ID={ids['operator_role']}",
    ]
    (LAB_DIR / "lab.env").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LAB_DIR / 'lab.env'}")


def main() -> int:
    load_dotenv()
    env = pg_env()
    app = goliathapp_checkout()
    sql_pg = app / "workflow_engine" / "sql_pg"

    ensure_engine_packages(app, env)
    run(["bash", str(sql_pg / "apply_schema.sh")], env)
    run([sys.executable, str(sql_pg / "seed_semantic_catalog.py")], env, cwd=app)
    run([sys.executable, str(sql_pg / "seed_action_catalog.py"), "--use-db"], env, cwd=app)

    with psycopg.connect(conninfo(env), autocommit=True) as conn:
        ids = bootstrap_people(conn)

    run(["psql", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(sql_pg / "seed_platform_nav_tree.sql")], env)

    portal_password = env.get("COURSE_PORTAL_DB_PASSWORD", "lab_portal_pw_change_me")
    with psycopg.connect(conninfo(env), autocommit=True) as conn:
        for key in ("scope_a", "scope_b"):
            grant_nav(conn, ids["operator_role"], ids[key])
        org_admin = int(scalar(conn, """SELECT "ID" FROM "RBAC"."Roles" WHERE "Name" = 'organization_admin'"""))
        grant_nav(conn, org_admin, ids["scope_a"])
        bootstrap_model(conn, ids)
        bootstrap_objects(conn, ids)
        conn.execute(
            psycopg.sql.SQL("ALTER ROLE goliath_portal WITH LOGIN PASSWORD {}").format(psycopg.sql.Literal(portal_password))
        )
        problems = conn.execute("SELECT count(*) FROM portal.fn_ledger_verify_all()").fetchone()
        if problems is not None:
            print(f"History ledgers checked: {problems[0]} problem(s)")

    write_lab_env(env, ids)
    print("Course lab ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
