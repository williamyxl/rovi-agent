"""Queue slot caps for debug and debug-scaling.

A queue may hold one running job and one queued job. A new submit is
allowed only when that queue has no queued job and at most one running
job. This module does not call qsub.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

ALLOWED_QUEUES = ("debug", "debug-scaling")
RUNNING_STATES = frozenset({"R"})
QUEUED_STATES = frozenset({"Q"})

_JOB_LINE = re.compile(
    r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+([A-Z])\s+(\S+)\s*$"
)


@dataclass(frozen=True)
class QueueCounts:
    running: int = 0
    queued: int = 0


def submission_allowed(n_running: int, n_queued: int) -> bool:
    """True when one more qsub stays inside one running plus one queued."""
    return n_running <= 1 and n_queued == 0


def parse_qstat(text: str, queue: str) -> QueueCounts:
    if queue not in ALLOWED_QUEUES:
        raise ValueError(f"queue not allowed: {queue}")
    running = 0
    queued = 0
    for raw in text.splitlines():
        line = raw.strip()
        match = _JOB_LINE.match(line)
        if match is None:
            continue
        state, job_queue = match.group(5), match.group(6)
        if job_queue != queue:
            continue
        if state in RUNNING_STATES:
            running += 1
        elif state in QUEUED_STATES:
            queued += 1
    return QueueCounts(running=running, queued=queued)


def qstat_user(user: str) -> str:
    completed = subprocess.run(
        ["qstat", "-u", user],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "qstat failed")
    return completed.stdout
