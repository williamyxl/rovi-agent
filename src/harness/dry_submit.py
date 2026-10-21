"""Print the phase-0 submission plan. This process never calls qsub."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from harness.cases import FIRST_CASE, SERVER_PBS, case_pbs
from harness.slots import parse_qstat, qstat_user, submission_allowed


def describe(path: Path) -> str:
    queue = walltime = nodes = None
    for line in path.read_text().splitlines():
        if line.startswith("#PBS -q "):
            queue = line.split()[-1]
        elif line.startswith("#PBS -l walltime="):
            walltime = line.split("=", 1)[1].strip()
        elif line.startswith("#PBS -l select="):
            nodes = line.split("=", 1)[1].strip()
    if queue is None or walltime is None or nodes is None:
        raise ValueError(f"incomplete PBS directives in {path}")
    return (
        f"queue={queue} select={nodes} walltime={walltime} "
        f"script={path.relative_to(ROOT)}"
    )


def plan_lines() -> list[str]:
    server = SERVER_PBS
    case = case_pbs(FIRST_CASE)
    return [
        "dry-plan: not submitted",
        f"1 debug-server {describe(server)}",
        f"2 debug-scaling-case software={FIRST_CASE} test_id=2 {describe(case)}",
    ]


def slot_lines(user: str) -> list[str]:
    text = qstat_user(user)
    lines = []
    for queue in ("debug", "debug-scaling"):
        counts = parse_qstat(text, queue)
        allowed = submission_allowed(counts.running, counts.queued)
        lines.append(
            f"slots {queue} running={counts.running} queued={counts.queued} "
            f"submit_allowed={str(allowed).lower()}"
        )
    return lines


def main() -> None:
    for line in plan_lines():
        if "qsub " in line:
            raise RuntimeError("dry plan must not contain a qsub command")
        print(line)
    user = os.environ.get("USER", "")
    if not user:
        print("slots skipped: USER is unset")
        return
    try:
        for line in slot_lines(user):
            print(line)
    except (OSError, RuntimeError) as exc:
        print(f"slots skipped: {exc}")


if __name__ == "__main__":
    main()
