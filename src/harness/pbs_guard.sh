# Source from a PBS script or run.sh. Exits 2 on a login shell.
if [[ -z "${PBS_JOBID:-}" || "${PBS_ENVIRONMENT:-}" != "PBS_BATCH" ]]; then
  echo "refusing: computational workload runs only inside a PBS batch job" >&2
  exit 2
fi
