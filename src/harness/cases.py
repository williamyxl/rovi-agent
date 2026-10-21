"""Registry cases the login script may name. No scientific imports."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "third_party" / "battery_sim_agent"
YAML_DIR = AGENT / "generate_simulated_data" / "output"

CASES = {
    "bsa_first_cycle": {
        "pipeline_name": "first_cycle_pipeline",
        "test_id": "2",
        "yaml_name": "simulated_data_setting_single_new_filtered.yaml",
        "queue": "debug-scaling",
        "nodes": 1,
        "walltime": "01:00:00",
    },
    "bsa_degradation": {
        "pipeline_name": "degradation_pipeline",
        "test_id": "1",
        "yaml_name": "simulated_data_setting_SEI.yaml",
        "queue": "debug-scaling",
        "nodes": 1,
        "walltime": "01:00:00",
    },
    "bsa_multi": {
        "pipeline_name": "first_cycle_pipeline",
        "test_id": "4",
        "yaml_name": "simulated_data_setting_multi_new_filtered.yaml",
        "queue": "debug-scaling",
        "nodes": 1,
        "walltime": "01:00:00",
    },
}

SERVER_PBS = ROOT / "llm" / "serve_gptoss_debug.pbs"
FIRST_CASE = "bsa_first_cycle"


def case_pbs(software: str) -> Path:
    if software not in CASES:
        raise KeyError(software)
    return ROOT / "registry" / software / "template.pbs"


def case_yaml(software: str) -> Path:
    return YAML_DIR / CASES[software]["yaml_name"]
