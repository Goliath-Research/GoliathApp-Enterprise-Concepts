"""Module 10 checks against the local course lab. Skipped, with the reason, when no lab is set up."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.usefixtures("lab")



import importlib.util  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parents[1]


def _support():
    spec = importlib.util.spec_from_file_location("module_10_support", HERE / "module_10_support.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["module_10_support"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lab() -> None:  # the simulator needs no database
    return None


def test_every_task_completes_despite_crashes() -> None:
    sim = _support().simulate(tasks=40, workers=4, lease_seconds=10, crash_rate=0.3, seed=7)
    assert sim.completed == 40
    assert sim.reclaimed > 0


def test_no_task_is_held_by_two_live_leases() -> None:
    sim = _support().simulate(tasks=25, workers=5, lease_seconds=5, crash_rate=0.5, seed=3)
    assert sim.max_concurrent_holders_per_task == 1
