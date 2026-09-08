import multiprocessing
import os
import sys
import time
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from md_to_docx import Template
from md_to_docx.mermaid import (
    ConvertError,
    render_mermaid_to_png,
    reset_launch_health,
)
import md_to_docx.mermaid as mermaid_mod


def _worker_fn(barrier, counter, out_file):
    def failing_run(*args, **kwargs):
        with counter.get_lock():
            counter.value += 1
        time.sleep(0.05)  # Simulate crash delay
        raise ConvertError("Failed to launch the browser process: simulated launch crash")

    mermaid_mod._run_mmdc = failing_run
    tmpl = Template.load("purple_book")

    barrier.wait(timeout=5)
    try:
        render_mermaid_to_png("graph TD;A-->B;", out_file, tmpl)
    except ConvertError:
        pass


def test_p0c_multiprocess_circuit_breaker_allows_at_most_one_launch_attempt(tmp_path, monkeypatch):
    health_file = tmp_path / "health.json"
    monkeypatch.setenv("MD2DOCX_MERMAID_HEALTH_FILE", str(health_file))
    reset_launch_health()

    barrier = multiprocessing.Barrier(3)
    counter = multiprocessing.Value("i", 0)

    workers = []
    for i in range(3):
        out_file = tmp_path / f"out_{i}.png"
        p = multiprocessing.Process(
            target=_worker_fn,
            args=(barrier, counter, out_file),
        )
        workers.append(p)
        p.start()

    for p in workers:
        p.join(timeout=5)

    # Across 3 concurrent worker processes, exactly ONE should attempt launch;
    # the other two must be blocked BEFORE calling _run_mmdc!
    assert counter.value == 1, f"Expected exactly 1 launch attempt across workers, but got {counter.value}"
