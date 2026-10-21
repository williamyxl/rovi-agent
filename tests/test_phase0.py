"""Phase 0: dry plan, slot cap, and login-node refusal."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SRC = str(ROOT / "src")


def run(cmd, env=None, cwd=None):
    merged = os.environ.copy()
    merged.pop("PBS_JOBID", None)
    merged.pop("PBS_ENVIRONMENT", None)
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


class Phase0Test(unittest.TestCase):
    def test_dry_plan_lists_two_jobs_and_does_not_submit(self):
        completed = run([PY, "-m", "harness.dry_submit"], env={"PYTHONPATH": SRC})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = completed.stdout
        self.assertIn("dry-plan: not submitted", text)
        self.assertIn("queue=debug select=1 walltime=01:00:00", text)
        self.assertIn("queue=debug-scaling select=1 walltime=01:00:00", text)
        self.assertIn("software=bsa_first_cycle test_id=2", text)
        self.assertNotIn("qsub ", text)
        self.assertEqual(text.count("queue=debug "), 1)
        self.assertEqual(text.count("queue=debug-scaling "), 1)

    def test_slot_cap_refuses_a_queued_job(self):
        sys.path.insert(0, SRC)
        from harness.slots import parse_qstat, submission_allowed

        sample = textwrap.dedent(
            """\
            Job id                 Name             User              Time Use S Queue
            -------------------    ---------------- ----------------  -------- - -----
            1.aurora               gptoss-api       user                     0 R debug
            2.aurora               bsa-first        user                     0 Q debug-scaling
            3.aurora               other            user                     0 R workq
            """
        )
        debug = parse_qstat(sample, "debug")
        scaling = parse_qstat(sample, "debug-scaling")
        self.assertEqual((debug.running, debug.queued), (1, 0))
        self.assertEqual((scaling.running, scaling.queued), (0, 1))
        self.assertTrue(submission_allowed(debug.running, debug.queued))
        self.assertFalse(submission_allowed(scaling.running, scaling.queued))
        self.assertFalse(submission_allowed(1, 1))
        self.assertFalse(submission_allowed(2, 0))

    def test_server_refuses_on_login_before_module_load(self):
        script = ROOT / "llm" / "serve_gptoss_debug.pbs"
        text = script.read_text()
        guard_at = text.index("pbs_guard.sh")
        module_at = text.index("module load frameworks")
        vllm_at = text.index('"$VLLM" serve')
        self.assertLess(guard_at, module_at)
        self.assertLess(guard_at, vllm_at)
        completed = run(["bash", str(script)])
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("refusing:", completed.stderr)
        self.assertNotIn("module load", completed.stdout)

    def test_worker_refuses_on_login_before_pybamm(self):
        completed = run(["bash", str(ROOT / "registry" / "bsa_first_cycle" / "run.sh")])
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("refusing:", completed.stderr)
        probe = run(
            [
                PY,
                "-c",
                "import harness.worker_entry as w; w.main()",
            ],
            env={"PYTHONPATH": SRC},
        )
        self.assertEqual(probe.returncode, 2, probe.stderr)
        self.assertIn("refusing:", probe.stderr)
        self.assertNotIn("pybamm", probe.stderr)
        self.assertNotIn("torch", probe.stderr)
        self.assertNotIn("vllm", probe.stderr)
        imported = run(
            [
                PY,
                "-c",
                (
                    "import sys; import harness.worker_entry as w\n"
                    "try:\n"
                    "    w.main()\n"
                    "except SystemExit:\n"
                    "    pass\n"
                    "bad = [n for n in ('pybamm','torch','vllm') if n in sys.modules]\n"
                    "raise SystemExit(3 if bad else 0)\n"
                ),
            ],
            env={"PYTHONPATH": SRC},
        )
        self.assertEqual(imported.returncode, 0, imported.stderr)

    def test_load_balancer_refuses_on_login(self):
        completed = run([PY, str(ROOT / "llm" / "lb.py"), "--port", "9", "--backends", "http://127.0.0.1:1"])
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("refusing:", completed.stderr)

    def test_next_job_does_not_submit(self):
        sys.path.insert(0, SRC)
        from harness.next_job import write_next_job

        run_dir = ROOT / "runs" / "phase0-next"
        path = write_next_job(run_dir, "bsa_degradation")
        text = path.read_text()
        self.assertIn('"qsub": false', text)
        self.assertIn("debug-scaling", text)
        self.assertNotIn("qsub ", text)

    def test_no_runtime_path_outside_project(self):
        banned = "alcf-aurora-llm"
        allowed = {"stage_weights.sh", "serve_gptoss_debug.pbs"}
        roots = [ROOT / "src", ROOT / "llm", ROOT / "registry"]
        for base in roots:
            for path in base.rglob("*"):
                if path.suffix not in {".py", ".pbs", ".sh"}:
                    continue
                if path.name in allowed:
                    continue
                text = path.read_text()
                self.assertNotIn(banned, text, str(path))


if __name__ == "__main__":
    unittest.main()
