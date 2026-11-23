"""Course lab control: start the PostgreSQL 19 lab, build it from GoliathApp's official scripts, reset it.

    python course_lab.py up        start postgres:19-bookworm on 127.0.0.1 (compose.yaml)
    python course_lab.py setup     apply GoliathApp schema + seeds, then course data (lab/setup_lab.py)
    python course_lab.py status    show whether the lab is reachable and set up
    python course_lab.py psql      open psql on the lab
    python course_lab.py down      stop the lab (keeps data)
    python course_lab.py reset     stop the lab and delete its volume and .lab/lab.env

    python course_lab.py learner up|down   one private lab per OS user on a shared machine
                                           (compose.learner.yaml, free port 54500-54599)

Everything stays on this machine: the database binds to loopback, and setup refuses non-local hosts.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT / ".lab"


def _load_env() -> None:
    for path in (ROOT / ".env",):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _compose(*args: str, file: str = "compose.yaml", project: str | None = None, env: dict[str, str] | None = None) -> int:
    if shutil.which("docker") is None:
        print("Docker is required for the lab database (https://docs.docker.com/get-docker/).", file=sys.stderr)
        return 2
    cmd = ["docker", "compose", "-f", str(ROOT / file)]
    if project:
        cmd += ["-p", project]
    cmd += list(args)
    return subprocess.run(cmd, cwd=ROOT, env=env or os.environ.copy()).returncode


def _free_port(lo: int = 54500, hi: int = 54599) -> int:
    for port in range(lo, hi + 1):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("no free port in 54500-54599")


def _learner(action: str) -> int:
    user = re.sub(r"[^a-z0-9]", "", getpass.getuser().lower()) or "learner"
    project = f"goliathapp-{user}"
    state = LAB / "learner.env"
    LAB.mkdir(exist_ok=True)
    values: dict[str, str] = {}
    if state.exists():
        values = dict(line.split("=", 1) for line in state.read_text().splitlines() if "=" in line)
    if action == "up":
        values.setdefault("LEARNER_PG_PORT", str(_free_port()))
        values.setdefault("POSTGRES_PASSWORD", secrets.token_urlsafe(18))
        state.write_text("".join(f"{k}={v}\n" for k, v in values.items()))
        state.chmod(0o600)
        env = {**os.environ, **values}
        rc = _compose("up", "-d", "--wait", file="compose.learner.yaml", project=project, env=env)
        if rc == 0:
            print(f"Your lab: 127.0.0.1:{values['LEARNER_PG_PORT']}. Point .env at it "
                  f"(PGPORT={values['LEARNER_PG_PORT']}, PGPASSWORD from {state}), then run: python course_lab.py setup")
        return rc
    env = {**os.environ, **values} if values else {**os.environ, "LEARNER_PG_PORT": "0", "POSTGRES_PASSWORD": "x"}
    rc = _compose("down", "-v", file="compose.learner.yaml", project=project, env=env)
    state.unlink(missing_ok=True)
    return rc


def _status() -> int:
    sys.path.insert(0, str(ROOT))
    from course_support import lab_ready

    ok, reason = lab_ready()
    print("Course lab ready." if ok else reason)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    _load_env()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["up", "setup", "status", "psql", "down", "reset", "learner"])
    p.add_argument("action", nargs="?", choices=["up", "down"])
    a = p.parse_args(argv)
    if a.command == "up":
        return _compose("up", "-d", "--wait")
    if a.command == "down":
        return _compose("down")
    if a.command == "reset":
        rc = _compose("down", "-v")
        (LAB / "lab.env").unlink(missing_ok=True)
        return rc
    if a.command == "setup":
        return subprocess.run([sys.executable, str(ROOT / "lab" / "setup_lab.py")], cwd=ROOT).returncode
    if a.command == "status":
        return _status()
    if a.command == "psql":
        return subprocess.run(["psql"], env=os.environ.copy()).returncode
    if a.command == "learner":
        return _learner(a.action or "up")
    return 1


if __name__ == "__main__":
    sys.exit(main())
