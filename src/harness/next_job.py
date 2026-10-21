"""Record a follow-up case. The login node is the only qsub caller."""

from __future__ import annotations

import json
from pathlib import Path

from harness.cases import CASES


def write_next_job(run_dir: Path, software: str) -> Path:
    if software not in CASES:
        raise KeyError(software)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "next_job.json"
    payload = {
        "software": software,
        "queue": CASES[software]["queue"],
        "nodes": CASES[software]["nodes"],
        "walltime": CASES[software]["walltime"],
        "test_id": CASES[software]["test_id"],
        "qsub": False,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
