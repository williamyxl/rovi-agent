#!/bin/bash
# Confirm the gpt-oss-120b checkpoint this project serves. Does not copy or symlink.
set -o pipefail
MODEL=/lus/flare/projects/MatSciAI/xiaoliyan/workdir/alcf-aurora-llm/gpt-oss-120b/models/openai-gpt-oss-120b
CACHE=/lus/flare/projects/MatSciAI/xiaoliyan/workdir/alcf-aurora-llm/gpt-oss-120b/.tiktoken_cache
[[ -f "$MODEL/config.json" ]] || { echo "ERROR: missing $MODEL/config.json"; exit 2; }
[[ -d "$CACHE" ]] || { echo "ERROR: missing $CACHE"; exit 2; }
echo "checkpoint=$MODEL"
echo "tiktoken_cache=$CACHE"
exit 0
