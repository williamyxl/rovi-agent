"""Refuse GPU and CPU entry points unless this process is a PBS batch job.

Importing this module does not import pybamm, torch, or vllm.
"""

from __future__ import annotations

import os
import sys

REFUSAL = (
    "refusing: computational workload runs only inside a PBS batch job"
)


def pbs_batch_ok() -> bool:
    job_id = os.environ.get("PBS_JOBID", "").strip()
    environment = os.environ.get("PBS_ENVIRONMENT", "").strip()
    return bool(job_id) and environment == "PBS_BATCH"


def require_pbs_batch() -> None:
    if pbs_batch_ok():
        return
    sys.stderr.write(REFUSAL + "\n")
    raise SystemExit(2)
