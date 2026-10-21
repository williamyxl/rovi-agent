#!/bin/bash
set -o pipefail
ROOT=/lus/flare/projects/MatSciAI/xiaoliyan/workdir/rovi-battery-data-ai
source "$ROOT/src/harness/pbs_guard.sh"
exec /usr/bin/python3.11 "$ROOT/src/harness/worker_entry.py" --software bsa_degradation
