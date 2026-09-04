#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

narrate() {
  printf '\n\033[1;36m%s\033[0m\n' "$1"
  sleep 1
}

run() {
  printf '\n\033[2m$'
  for arg in "$@"; do
    printf ' %s' "$arg"
  done
  printf '\033[0m\n'
  sleep 0.8
  "$@"
  sleep 1
}

QUESTION="Inspect the actual images of The Japanese Footbridge and Flower Beds in Holland. Compare their edge cropping, depth cues, and directional brushwork, then explain which better supports a quiet contemplative room."

printf '\033[2J\033[H'
printf '\033[1mPOLIGN MULTI-COLLECTION + MULTIMODAL RAG\033[0m\n'
printf 'memory -> scoped candidates -> visual cache -> research -> review -> summary\n'

narrate "1. Four independent collections in one durable Polign database"
run .venv/bin/polign-curator collections

narrate "2. Curator preferences live in memory, not model context"
run .venv/bin/polign-curator memories --history

narrate "3. Replay the verified live run; cached observations avoided re-sending images"
printf '\n\033[2m$ polign-curator ask --summary "%s"\033[0m\n' "$QUESTION"
sleep 1
sed -n '1,200p' demo/reviewed-run.txt
sleep 2

narrate "4. The visual observations remain durable in their own collection"
run .venv/bin/polign-curator collections

printf '\n\033[1;32mDone: filtered retrieval, multimodal evidence, independent review, final summary.\033[0m\n'
