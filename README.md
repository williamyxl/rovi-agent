# rovi-agent

Aurora harness for battery charge capacity versus cycle number. An open-weight model reads a token stream and selects a registered program. PyBaMM produces the capacity numbers. The login node only submits PBS jobs and copies finished files.

This tree is the code for [williamyxl/rovi-agent](https://github.com/williamyxl/rovi-agent). The working copy on Aurora is `rovi-battery-data-ai`.

## What runs where

| Piece | Where | Role |
|---|---|---|
| Login node | Aurora login | `qsub`, `qstat`, `qdel`, and copy finished text into a report. No model load, no PyBaMM, no token stream. |
| `llm/serve_gptoss_debug.pbs` | `debug`, 1 node, 1 hour | gpt-oss-120b on Intel GPUs. Three vLLM engines, tensor-parallel 4, one load balancer. |
| `registry/bsa_*` | `debug-scaling`, 1 node, 1 hour | One Battery-Sim-Agent case. PyBaMM stays on CPUs. |

Each of those queues may hold one running job and one queued job. GPU and CPU entry points exit unless `PBS_JOBID` is set and `PBS_ENVIRONMENT` is `PBS_BATCH`.

The checkpoint is not in this repository. The server reads it in place:

`alcf-aurora-llm/gpt-oss-120b/models/openai-gpt-oss-120b`

The harmony vocab cache beside that checkpoint is read the same way. Those files keep their own license. OpenAI distributes gpt-oss weights under Apache-2.0.

## Relationship to existing work

**Battery-Sim-Agent** ([opqrst-chen/Battery-Sim-Agent](https://github.com/opqrst-chen/Battery-Sim-Agent), MIT, Copyright 2026 Opqrst) is the first scientific program. `third_party/battery_sim_agent/` is a copy of its pipelines, PyBaMM runner, prompts, and the three yaml case sets used here (`bsa_first_cycle`, `bsa_degradation`, `bsa_multi`). Upstream commit `354f2dd`. Its license file stays in that directory. This project does not relicense that copy. The harness adds a PBS guard and runs one yaml id per job. Upstream runs PyBaMM in a local process pool.

**Aurora gpt-oss serving** ([williamyxl/alcf-aurora-llm](https://github.com/williamyxl/alcf-aurora-llm)) is the source of the serving layout. `llm/serve_gptoss_debug.pbs` and `llm/lb.py` are adapted from `api_serve_high_concurrency/serve_gptoss_capacity.pbs` and the campaign load balancer. The adaptation changes the queue from `capacity` to `debug` and the walltime from 24 hours to 1 hour, and it refuses to start outside a PBS batch job. That campaign repository has no license file. The adapted scripts in this repository are covered by the license below.

**ChemGraph** and the other materials agents surveyed in `PLAN.md` are not dependencies. They are not imported.

**PyBaMM** is an external dependency of the vendored runner (`pybamm==25.6.0`, BSD-3). It is not vendored here.

## Layout

```
PLAN.md                 design and phase status
src/harness/            slot caps, dry submit, PBS guard, worker entry
registry/bsa_*/         one PBS job per Battery-Sim-Agent case
llm/                    serve script and load balancer
third_party/battery_sim_agent/   MIT upstream copy
tests/test_phase0.py    login-node refusal and dry plan
```

Phase 0 is in the tree. No science job has been submitted. `python3.11 -m harness.dry_submit` prints one `debug` server and one `debug-scaling` case and does not call `qsub`.

## License

The harness, registry, tests, serve-script adaptation, and this documentation are under the MIT License, Copyright (c) 2026 Xiaoli Yan. See [LICENSE](LICENSE).

The Battery-Sim-Agent copy remains under the MIT License, Copyright (c) 2026 Opqrst. See [third_party/battery_sim_agent/LICENSE](third_party/battery_sim_agent/LICENSE).
