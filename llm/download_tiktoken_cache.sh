#!/bin/bash
# One-time vocab fetch for gpt-oss. Does not start vLLM or PyBaMM.
# Phase 0 does not run this script. It writes files under this project's models/.
set -o pipefail
ROOT=/lus/flare/projects/MatSciAI/xiaoliyan/workdir/rovi-battery-data-ai
export http_proxy="${http_proxy:-http://proxy.alcf.anl.gov:3128}"
export https_proxy="${https_proxy:-http://proxy.alcf.anl.gov:3128}"
export TIKTOKEN_RS_CACHE_DIR="${TIKTOKEN_RS_CACHE_DIR:-$ROOT/models/.tiktoken_cache}"
mkdir -p "$TIKTOKEN_RS_CACHE_DIR"
module use /opt/aurora/26.26.0/frameworks/modulefiles
module load frameworks
FWPY=/opt/aurora/26.26.0/frameworks/aurora_frameworks-2025.3.1/bin/python
echo "Downloading harmony vocab -> $TIKTOKEN_RS_CACHE_DIR"
"$FWPY" -c "
import openai_harmony as oh
oh.load_harmony_encoding(oh.HarmonyEncodingName.HARMONY_GPT_OSS)
print('HARMONY_CACHE_OK')
"
echo "Cached files:"
ls -lh "$TIKTOKEN_RS_CACHE_DIR"
