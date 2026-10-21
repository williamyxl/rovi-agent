"""Battery-Sim-Agent entry point. PBS check runs before any scientific import."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from harness.cases import CASES, case_yaml  # noqa: E402
from harness.pbs_guard import require_pbs_batch  # noqa: E402


def main() -> None:
    require_pbs_batch()
    parser = argparse.ArgumentParser()
    parser.add_argument("--software", required=True, choices=sorted(CASES))
    args = parser.parse_args()
    spec = CASES[args.software]
    agent_root = ROOT / "third_party" / "battery_sim_agent" / "battery_agent"
    sys.path.insert(0, str(agent_root))
    os.chdir(agent_root)
    sys.argv = [
        "pipeline.py",
        "--pipeline_name",
        spec["pipeline_name"],
        "--test_id",
        spec["test_id"],
        "--yaml_path",
        str(case_yaml(args.software)),
    ]
    import pipeline as bsa_pipeline

    bsa_pipeline.main()


if __name__ == "__main__":
    main()
