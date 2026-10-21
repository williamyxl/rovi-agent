# Plan: token-driven Aurora harness for battery charge-capacity work

Status: phase 0 is in the tree. No job has been submitted. The token server reads the existing gpt-oss-120b checkpoint at `alcf-aurora-llm/gpt-oss-120b/models/openai-gpt-oss-120b`. That path is the only runtime dependency outside this project.

Project root (only place this work may live):

`/lus/flare/projects/MatSciAI/xiaoliyan/workdir/rovi-battery-data-ai`

Code that runs lives in this root. The one exception is the gpt-oss-120b checkpoint and its tiktoken cache under `alcf-aurora-llm/gpt-oss-120b/`, which the token server reads in place.

## 1. What is being built

An agentic harness. It is the product. Battery charge-capacity work is the first campaign it runs.

The harness:

1. Opens a streaming completion against an open-weight model and reads the token stream as it arrives.
2. From that stream, selects a software entry in a local registry. It does not accept free-form shell.
3. Writes the input files for that software from fields the stream supplied.
4. Submits the job to Aurora with `qsub` and a PBS template stored in this project.
5. Waits, then reads the job’s stdout, stderr, and declared output files.
6. Feeds that text back into the next completion.
7. Writes an analysis and compiles a report whose numbers are copied from the job outputs.

The model never calls `qsub`, never opens an arbitrary path, and never writes the report file by itself. The harness does those three things. The model’s only actuator is the token stream.

The science campaign that this loop has to carry is unchanged:

- Keep both charge capacity \(Q_\mathrm{ch}(n)\) and discharge capacity \(Q_\mathrm{dch}(n)\), plus Coulombic efficiency.
- Extract cited mechanisms for loss of charge capacity.
- Fit transferable \(Q(n)\) models across chemistries and protocols.
- Rank design changes only when a job output supports the rank.

The 120B model is not the fade predictor. Fade fits and PyBaMM runs are registry software. The model selects them and reads their outputs.

## 2. Existing materials harnesses

Survey date 2026-10-20. Sources are public repositories and docs. The local ChemGraph tree under `workdir/` was not opened. Nothing below is imported at runtime.

Compatibility means six checks against this plan: open-weight model, control by the raw token stream, closed software registry (no free shell), write inputs, Aurora `qsub` and read-back, and charge-capacity versus cycle number.

| Harness | License | What it already does | Fit |
|---|---|---|---|
| [ChemGraph](https://github.com/argonne-lcf/ChemGraph) (Argonne) | Apache-2.0 | LangGraph agent, ASE/RDKit tools, MCP. Deep Agent reads a `pbs-hpc` skill, writes a PBS file, calls `qsub`, and later reads `job.id` and outputs. OpenAI-compatible `base_url`. Docs name Aurora for distributed backends. The published PBS walkthrough is Polaris, and the docs say real agent-driven Polaris submission is still unvalidated. | Closest job loop. Wrong actuator: LangGraph tools plus a workspace shell, not a token fence. Adopting it would import a sibling project and give the model a shell. |
| [Battery-Sim-Agent](https://github.com/opqrst-chen/Battery-Sim-Agent) | MIT | Closed loop with PyBaMM for inverse electrochemical parameters, including an SEI degradation pipeline. OpenAI-compatible client. The authors’ runs use vLLM serving `gpt-oss-120b`. | Closest science and the same model endpoint. The simulator runs in-process (`ProcessPoolExecutor`), not as an Aurora job. The client consumes a finished chat message, not the token stream. |
| [Batterytwin-mcp](https://github.com/BinuShefieldShifani/Batterytwin-mcp) | MIT | PyBaMM tools over MCP, including `simulate_degradation` (SEI fade over N cycles). LangGraph ReAct plus a local Ollama model. | Useful tool list for the registry. MCP tool calls and a 7B Ollama model. No PBS. |
| [AtomisticSkills](https://github.com/learningmatter-mit/AtomisticSkills) | MIT | Skill and MCP catalog (MLIP, DFT via atomate2, databases). Campaigns include Li-ion solid-electrolyte design. The host is a coding agent (Cursor, Claude Code, and similar) with a shell. atomate2 remote jobs target NERSC-style HPC. | Registry shape matches `registry/<name>/`. The host is an IDE shell, not this token loop, and the science is atomistic rather than \(Q(n)\). |
| [MatClaw](https://github.com/DingyangLyu/MatClaw) | Apache-2.0 | Natural language to Python inside a Docker container. Large skill library, including battery topics. Can SSH to a cluster for VASP. LLM side is Anthropic-compatible. | Same “write, run, read, retry” story. Docker is not the Aurora execution path. The API dialect is not the vLLM OpenAI stream. The model writes arbitrary code. |
| [matsim-agents](https://github.com/ORNL/matsim-agents) | BSD-3 | LangGraph planner, MLIP relaxation, uncertainty gate, analyst report. Structured outputs. | Report node is a useful pattern. No PBS. No cycle-life data. Control is LangGraph structured output. |
| [LAMMPS-Agents](https://github.com/ANL-NST/LAMMPS-Agents) | MIT | Multi-agent LAMMPS setup with an HPC manager tool. | Different code and different physics. Not a token-stream harness. |
| [LLaMP](https://github.com/chiang-yuan/llamp) | BSD-style LBNL notice (GitHub license “Other”; OSTI lists BSD-3) | Hierarchical ReAct agents over the Materials Project API. | Grounds materials facts. It does not fit \(Q(n)\) curves or Aurora jobs, and it needs a Materials Project key and outbound network. |

No listed harness feeds on the raw token stream and submits Aurora jobs from a closed registry. That combination stays code we write under `src/harness/`.

What is worth copying as ideas, not as a dependency:

- From ChemGraph’s PBS skill: one run directory visible to login and compute nodes, save `job.id` even when submission looks uncertain, and do not treat `qstat` completion as scientific success.
- From Battery-Sim-Agent: the first software in this project. Its two pipelines (`first_cycle_pipeline`, `degradation_pipeline`), the PyBaMM runner, and the bounded parameter update are copied in under the MIT notice and run as Aurora jobs. Capacity numbers still come from PyBaMM, not from the model.
- From AtomisticSkills and MatClaw: one directory per software entry, with a schema and a fixed script. The model selects the entry. It does not author the script.
- From matsim-agents: a deterministic report skeleton when the model text and the artifact numbers disagree.

ChemGraph is not installed. Battery-Sim-Agent’s functions are copied into this project from the public MIT repository. The copy does not live in, or import from, any other `workdir` folder.

## 3. Token interface

The token server is a concurrent one-node job. It uses the existing gpt-oss-120b recipe in `alcf-aurora-llm/api_serve_high_concurrency/serve_gptoss_capacity.pbs` (3× vLLM, tensor-parallel 4, tiles 0–3 / 4–7 / 8–11, one load balancer on port 8000, model `gpt-oss-120b`). The script that runs lives under `llm/` in this project. Logs stay here. The weights stay at `alcf-aurora-llm/gpt-oss-120b/models/openai-gpt-oss-120b`, and the harmony vocab cache next to that checkpoint is the one the server reads.

Two fields in the reference must change. The reference asks for `-q capacity` and `walltime=24:00:00`. This project submits `-q debug`, `select=1`, `walltime=01:00:00`. The Intel GPU layout stays: Aurora `frameworks` vLLM on the PVC tiles, `ZE_AFFINITY_MASK` per engine. No CUDA.

The server job writes `llm/ENDPOINT.txt` (node IP and `http://<ip>:8000/v1`). Battery-Sim-Agent jobs on the other queue call that URL. Compute nodes have no public address; the worker reaches the server over the intra-cluster IP. The login node does not load weights, open the token stream, or start an engine.

Weight load takes several minutes of the one-hour slot. Workers start only after `ENDPOINT.txt` answers `/v1/models`. The single queued `debug` slot may hold the next server job so it starts when the current one hits the walltime. Callers retry across that gap.

Client behavior, inside the `debug-scaling` job only:

- Request `stream: true`. Read server-sent events. Append each `delta.content` as soon as it arrives. Do not wait for the final message to decide whether an action has already closed.
- Log the stream verbatim under the run directory (text, and token counts from the final usage chunk). That log is the record of what the model actually emitted.
- gpt-oss uses the harmony channel format. The harness acts only on a closed action fence in the visible content. Analysis-channel prose is stored and is not executed.
- OpenAI `tool_calls` JSON is not the control plane. Tool-call parsers differ across vLLM and llama.cpp and have already been a failure point for this model family. A fence the stream decoder can see is the control plane, so the same harness works against either server.

Action fence, detected incrementally:

```
<<<action
{"op":"submit","software":"bsa_first_cycle","inputs":{"test_id":2,"queue":"debug-scaling","nodes":1,"walltime":"01:00:00"}}
>>>
```

One completion may contain several fenced actions. On each `>>>` the harness validates, executes, and either continues reading or stops the completion and starts the next turn with the observation. If the fence does not parse, the harness returns the parse error as the next observation and does not submit anything.

Allowed `op` values:

| op | Harness does |
|---|---|
| `select` | Checks `software` against the registry. Returns the input schema and the PBS limits. Writes nothing. |
| `write` | Writes one file under this run’s `inputs/` from registry-validated fields. |
| `submit` | Writes `runs/<id>/next_job.json` with the registry id. Does not call `qsub`. The login script is the only submitter, and only when that queue’s slot cap allows it. |
| `read` | After the job ends, returns capped stdout, stderr, and declared artifacts. |
| `analyze` | Asks for the next completion with those artifacts in the prompt. No side effect by itself. |
| `report` | Compiles the report file from the run record plus the analysis text. |

Anything outside this list is rejected and returned to the model as an observation.

## 4. Registry, files, jobs, reports

### Software registry

Each entry is a directory under `registry/<name>/`:

- `software.toml` — id, what question it answers, input schema, output globs, walltime, node count, queue, module line.
- `template.pbs` — PBS skeleton. Placeholders only for fields the schema allows.
- `run.sh` or a declared command — the program inside the job. The model does not supply this command.

First entries, in implementation order. Each worker entry is a Battery-Sim-Agent function, queue `debug-scaling`, one node, walltime at most one hour, CPU only:

1. `bsa_first_cycle` — `first_cycle_pipeline` for one single-parameter yaml id (`Chen2020`, DFN).
2. `bsa_degradation` — `degradation_pipeline` for one SEI yaml id.
3. `bsa_multi` — one multi-parameter yaml id, same runner, after the first two return a curve.

`curve_fit` and `transfer_split` stay later. They are not required to bring Battery-Sim-Agent up.

Adding a program means adding a registry entry. The model cannot point at a path outside `registry/`.

### Input files

The harness creates `runs/<run_id>/inputs/`. Paths in the action must stay under that directory. The schema rejects unknown keys, wrong types, and values outside declared bounds (cycle count, temperature, voltage window, walltime). The file on disk is what the job reads. The token text is not re-read by the scientific program.

### Aurora queues

Only `debug` and `debug-scaling`. Account `MatSciAI`, `filesystems=flare`. Requested walltime is at most `01:00:00` on every job.

| Queue | What runs there | Nodes | Slots this project may hold |
|---|---|---|---|
| `debug` | gpt-oss-120b token server (Intel GPUs) | exactly 1 | 1 running and 1 queued |
| `debug-scaling` | Battery-Sim-Agent functions and PyBaMM | 1 by default, at most 256 | 1 running and 1 queued |

The two running jobs are concurrent: the model stays up on `debug` while one Battery-Sim-Agent case runs on `debug-scaling`. They cannot share a queue, because each queue allows only one running job.

Before every `qsub`, the submitter counts this user’s jobs in that queue. If one is already running and one is already queued, it does not submit. The queued `debug` job is only the next token server. The queued `debug-scaling` job is only the next Battery-Sim-Agent case. No job arrays. One `qsub` is one job id.

`debug-scaling` stays at `select=1` for a single PyBaMM case. A later entry may request up to 256 nodes only as one job id, with the node count written in that registry entry. The first cases do not.

### Login node

No live computational workload runs on the login node. That covers GPU work and CPU work: model load, token generation, PyBaMM, CasADi, curve fits, and the Battery-Sim-Agent loop.

The login process may only:

- enforce the slot caps
- call `qsub`, `qstat`, and `qdel` on this project’s jobs
- read and write small text files that are already on the shared filesystem (`ENDPOINT.txt`, job ids, PBS logs, finished artifacts)
- assemble `report.md` by copying those files. It does not call the model to write the analysis, and it does not recompute a capacity or a residual

Every GPU or CPU entry point (`llm/` server, `third_party/battery_sim_agent`, `registry/*/run.sh`) exits immediately unless `PBS_JOBID` is set and `PBS_ENVIRONMENT` is `PBS_BATCH`. A login shell does not have those variables. The check runs before any import of `pybamm`, `torch`, `vllm`, or the model weights. Phase 0 includes a test that invoking a worker entry on the login node exits with that refusal and does not start a solver.

### Where each function runs

Battery-Sim-Agent today runs PyBaMM in a local process pool and calls a finished chat completion. Here the split is:

- **Login node.** Submit and file copy only, as listed above.
- **`debug` node.** Token server. All GPU work is this process: Intel Data Center GPU Max (PVC) via the vendored vLLM recipe. A startup check must show XPU devices. A CUDA context is a failed server job.
- **`debug-scaling` node.** One Battery-Sim-Agent case: `first_cycle_pipeline` or `degradation_pipeline` for one yaml id. PyBaMM (`pybamm==25.6.0`, IDAKLU / CasADi) runs on the node’s CPUs. The token client and the action-fence parser run in this same job and stream from `llm/ENDPOINT.txt`. The job does not call `qsub`.

PyBaMM is not a GPU code. It is not moved onto the PVC tiles. Any Battery-Sim-Agent path that initializes CUDA is left out of the copy. The only GPU program in the first version is the gpt-oss-120b server.

One case must finish inside one hour, including token wait. A long SEI study is a chain of one-case jobs through the single `debug-scaling` queued slot, not one multi-hour job.

### Aurora submit and read

The login submitter is the only `qsub` caller. The model never calls it.

After `qsub`, the submitter polls that job id. On completion it reads `runs/<run_id>/outputs/` and the PBS stdout/stderr, each truncated to a declared byte cap, with the cap stated so the model knows it did not see the whole log. A non-zero exit or a missing declared output is a failed observation. The submitter does not rewrite the input on its own.

### Analysis and report

When the model emits `report`, the harness writes `runs/<run_id>/report.md` with a fixed skeleton:

- question asked
- software id and registry version
- input file hash
- job id, queue, walltime used, exit code
- tables and scalars copied from declared artifacts
- a marked analysis section containing the model’s text
- a flag on any number in that analysis that does not appear in the artifacts

The skeleton is produced by code on the login node from files the compute job already wrote. The analysis paragraph is the only model-authored part, and the model writes it inside the `debug-scaling` job.

## 5. Science the harness is for

Capacity leaves a cell for a small set of reasons. Registry outputs and reports use this vocabulary (Dubarry degradation modes):

| Mode | What is lost | Signatures the jobs should compute | Design levers |
|---|---|---|---|
| SEI growth | Cyclable lithium | CE < 1, early fade near \(\sqrt{n}\), resistance rise | Formation, additives, anode surface, temperature |
| Lithium plating | Cyclable lithium | Knee after fast charge or low \(T\), CE drop | N/P ratio, porosity, charge protocol |
| Loss of active material | Electrode sites | dQ/dV peak loss, gap between low-rate and use-rate capacity | Particle size, voltage limits, calendering |
| Transition-metal dissolution and crosstalk | Cathode sites and anode SEI | High-voltage fade, chemistry-specific | Upper cutoff, coatings, electrolyte |
| Impedance growth | Apparent capacity at the test rate | Capacity partly returns at a lower rate | Thickness, temperature, electrolyte |

Data the jobs read live under this root:

- `data/open/` — public cycle files after a license line is recorded. First pair proposed: Severson LFP, then one layered-oxide set from Battery Archive.
- `data/sim/` — PyBaMM cases. The mechanism label is whatever the input file set, stored beside the curve.
- `data/closed/` — owner drop only. The harness does not fetch it.

Harmonized columns the fit jobs require: `source_id`, `cell_id`, chemistry, protocol (temperature, rates, voltage window), `n`, `q_charge_ah`, `q_discharge_ah`, `ce`. Transfer comparisons use \(Q(n)/Q(n_0)\), not raw ampere-hours.

A report from the `curve_fit` or `transfer_split` job is a negative result if the chemistry holdout fails. That report is still compiled.

Design reports may only recommend a change that a registry job varied (voltage window, temperature, rate, and, in PyBaMM, particle radius, thickness, porosity, SEI rate constant). The recommendation quotes the job’s retention number.

## 6. Layout

```
PLAN.md
third_party/battery_sim_agent/   MIT copy of the functions this project runs
registry/bsa_first_cycle/
registry/bsa_degradation/
registry/bsa_multi/
src/harness/             slot caps, qsub, file-only report assembly; stream reader runs under PBS only
llm/                     vendored serve PBS (debug, 1 h), load balancer, ENDPOINT.txt
models/                  unused for weights; checkpoint stays in alcf-aurora-llm
runs/                    one directory per case (tokens, inputs, outputs, report)
data/open/  data/sim/  data/closed/
docs/
```

## 7. Sequence

| Phase | Does | Done when |
|---|---|---|
| 0 | Done. Battery-Sim-Agent and the serve recipe are under this root. The serve script is `-q debug`, `select=1`, `walltime=01:00:00`. Slot-cap check refuses a submit when a job is already queued. GPU and CPU entry points exit without `PBS_JOBID`. | `python3.11 -m harness.dry_submit` lists one `debug` server and one `debug-scaling` case and does not call `qsub`. Login-node invocation of the worker, the server, and `llm/lb.py` exits 2 before PyBaMM, torch, or vLLM. The serve script’s model path is the existing gpt-oss-120b checkpoint. |
| 1 | Submit the token server. Confirm XPU, not CUDA, and a live `/v1/models`. | `llm/ENDPOINT.txt` is reachable from another Aurora node. Walltime on the script is 1 hour. |
| 2 | One `bsa_first_cycle` job on `debug-scaling` while that server is running. The case streams tokens and runs PyBaMM on CPU. | `runs/<id>/report.md` cites both job ids and copies capacity and voltage errors from the PyBaMM output. |
| 3 | One `bsa_degradation` case, then `bsa_multi`, still one running and one queued on `debug-scaling`. | Each case has its own report. A case that cannot finish in 1 hour is split, not given a longer walltime. |
| 4 | Public cycle tables and the later fit / transfer entries. | Those jobs use the same queues, caps, and token server. |

Phase 1 and phase 2 overlap on purpose: the server holds the `debug` running slot, the case holds the `debug-scaling` running slot.

## 8. Risks

- **The stream never closes a fence.** Cap tokens, return what was read, do not invent an action.
- **The model emits a command instead of a registry id.** Reject. Observation explains the registry.
- **A job hangs.** PBS walltime is the kill switch. The observation is the partial log plus the timeout.
- **Analysis invents a number.** The report compiler flags numbers absent from artifacts.
- **Capacity definitions differ across sources.** Fit jobs refuse a table that does not say whether the column is charge or discharge capacity.
- **One-hour server.** Weight load consumes the front of the `debug` slot. Workers wait for `/v1/models`. The queued successor server covers the next hour. There is a gap between them.
- **Slot cap.** A sweep that submits every yaml id at once will be rejected. One case runs, one case waits.
- **CUDA on a PVC node.** The server job fails if the engine comes up on CUDA. PyBaMM stays on CPU.
- **Login-node compute.** A missing `PBS_JOBID` check would let a pipeline run on the login node. The guard is in the entry point, before heavy imports. The login submitter does not import those libraries.
- **PyBaMM is not a commercial cell.** Reports say when a ranking is simulation-only.

## 9. Decisions

1. First software is Battery-Sim-Agent, copied into this project (MIT). ChemGraph is not the runtime.
2. Token server is gpt-oss-120b, the 3×TP=4 Intel XPU recipe, on `debug`, one node, walltime 1 hour.
3. Battery-Sim-Agent cases run on `debug-scaling` (one node until a registry entry says otherwise), concurrent with that server. PyBaMM stays on CPU.
4. Each of `debug` and `debug-scaling` holds at most one running job and one queued job. No other queues.
5. The action fence in §3 runs inside the `debug-scaling` job. The login node only submits and copies finished files.
6. No GPU or CPU computational workload runs on the login node. Entry points refuse to start unless they are inside a PBS batch job.
7. Severson LFP and a licensed Battery Archive layered-oxide set wait until phase 4. Closed data stays out until then.
8. Phase 0 is implemented. The token server uses the gpt-oss-120b checkpoint and tiktoken cache already under `alcf-aurora-llm/gpt-oss-120b/`. Phase 1 can submit without copying them.
