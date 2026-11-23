"""Shared helpers for the course labs, notebooks and tests.

Connections always go to the local course lab (see lab/setup_lab.py). Live tests skip, with a
reason, when the lab is not running or not set up, so the repository's tests also run offline.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "db", "postgres"}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env_file(ROOT / ".env")
_load_env_file(ROOT / ".lab" / "lab.env")


def lab_ids() -> dict[str, int]:
    """Ids written by lab/setup_lab.py (organizations, scopes, course users)."""
    keys = {
        "org_a": "COURSE_ORG_A_ID",
        "scope_a": "COURSE_SCOPE_A_ID",
        "org_b": "COURSE_ORG_B_ID",
        "scope_b": "COURSE_SCOPE_B_ID",
        "admin": "COURSE_ADMIN_USER_ID",
        "operator": "COURSE_OPERATOR_USER_ID",
        "outsider": "COURSE_OUTSIDER_USER_ID",
        "operator_role": "COURSE_OPERATOR_ROLE_ID",
    }
    return {k: int(os.environ[v]) for k, v in keys.items() if os.environ.get(v)}


def owner_conninfo() -> str:
    host = os.environ.get("PGHOST", "127.0.0.1")
    if host not in LOCAL_HOSTS:
        raise RuntimeError(f"course labs only connect to a local lab database, not {host!r}")
    return (
        f"host={host} port={os.environ.get('PGPORT', os.environ.get('PG_HOST_PORT', '54339'))} "
        f"dbname={os.environ.get('PGDATABASE', os.environ.get('POSTGRES_DB', 'goliathapp_lab'))} "
        f"user={os.environ.get('PGUSER', os.environ.get('POSTGRES_USER', 'postgres'))} "
        f"password={os.environ.get('PGPASSWORD', os.environ.get('POSTGRES_PASSWORD', ''))} connect_timeout=3"
    )


def portal_conninfo() -> str:
    """The least-privileged role the portal uses: EXECUTE on portal.* only, no table access."""
    base = owner_conninfo().split(" user=")[0]
    password = os.environ.get("COURSE_PORTAL_DB_PASSWORD", "lab_portal_pw_change_me")
    return f"{base} user=goliath_portal password={password} connect_timeout=3"


def lab_ready() -> tuple[bool, str]:
    try:
        import psycopg
    except ImportError:
        return False, "psycopg is not installed"
    try:
        with psycopg.connect(owner_conninfo(), autocommit=True) as conn:
            row = conn.execute(
                """SELECT count(*) FROM "Meta"."Classes" WHERE "Name" = 'acme_child/Instrument'"""
            ).fetchone()
    except Exception as exc:  # noqa: BLE001 - any connection problem means "no lab"
        return False, f"course lab database not reachable ({type(exc).__name__}); run: python course_lab.py up"
    if not row or row[0] == 0 or not lab_ids():
        return False, "course lab not set up; run: python course_lab.py setup"
    return True, ""


def require_lab() -> None:
    import pytest

    ok, reason = lab_ready()
    if not ok:
        pytest.skip(reason)


@contextmanager
def owner() -> Iterator[Any]:
    import psycopg

    with psycopg.connect(owner_conninfo(), autocommit=True) as conn:
        yield conn


@contextmanager
def portal() -> Iterator[Any]:
    import psycopg

    with psycopg.connect(portal_conninfo(), autocommit=True) as conn:
        yield conn


def has_function(conn: Any, signature: str) -> bool:
    row = conn.execute("SELECT to_regprocedure(%s) IS NOT NULL", (signature,)).fetchone()
    return bool(row and row[0])


def open_session(user_key: str, *, scope_key: str = "scope_a", role: str | None = None) -> str:
    """Open a portal session for a course user, the way the portal does after sign-in."""
    ids = lab_ids()
    with owner() as conn:
        row = conn.execute(
            "SELECT session_token FROM portal.sp_session_open(%s, %s)", (ids[user_key], ids[scope_key])
        ).fetchone()
        assert row is not None
        token = str(row[0])
        if role is None:
            conn.execute("SELECT * FROM portal.sp_session_auto_select_active_role(%s)", (token,))
        else:
            role_row = conn.execute('SELECT "ID" FROM "RBAC"."Roles" WHERE "Name" = %s', (role,)).fetchone()
            assert role_row is not None
            conn.execute("SELECT * FROM portal.sp_session_set_active_role(%s, %s)", (token, role_row[0]))
    return token


def class_id(conn: Any, name: str) -> int:
    row = conn.execute('SELECT "ID" FROM "Meta"."Classes" WHERE "Name" = %s', (name,)).fetchone()
    assert row is not None, f"class {name} not found"
    return int(row[0])


def goliathapp_dir() -> Path:
    """The GoliathApp checkout the lab was built from (GOLIATHAPP_SRC, or .lab/GoliathApp)."""
    src = os.environ.get("GOLIATHAPP_SRC")
    return Path(src).resolve() if src else ROOT / ".lab" / "GoliathApp"


def run_example_sql(relative: str) -> None:
    """Run one of GoliathApp's own SQL examples against the lab with psql (skips if unavailable)."""
    import shutil
    import subprocess

    import pytest

    path = goliathapp_dir() / "workflow_engine" / "sql_pg" / "examples" / relative
    if not path.exists():
        pytest.skip(f"GoliathApp example not found at {path} (run python course_lab.py setup)")
    if shutil.which("psql") is None:
        pytest.skip("psql is not installed")
    conn = dict(part.split("=", 1) for part in owner_conninfo().split())
    env = {**os.environ, "PGHOST": conn["host"], "PGPORT": conn["port"], "PGDATABASE": conn["dbname"],
           "PGUSER": conn["user"], "PGPASSWORD": conn["password"]}
    subprocess.run(["psql", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(path)], env=env, check=True, capture_output=True)
