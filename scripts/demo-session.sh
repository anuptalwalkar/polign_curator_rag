#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

narrate() {
  printf '\n\033[1;36m%s\033[0m\n' "$1"
  sleep 2
}

run() {
  printf '\n\033[2m$'
  for arg in "$@"; do
    printf ' %s' "$arg"
  done
  printf '\033[0m\n'
  sleep 1.2
  "$@"
  sleep 2
}

scene() {
  printf '\033[2J\033[H'
  printf '\033[2mPOLIGN CURATOR  /  COMPLEX RAG DEMO\033[0m\n\n'
}

trace() {
  sed -n '1,13p' demo/reviewed-run.txt | while IFS= read -r line; do
    case "$line" in
      *"passed=False"*) color='\033[1;33m' ;;
      *"passed=True"*) color='\033[1;32m' ;;
      *"reused visual_cache"*) color='\033[1;35m' ;;
      *"visual decision"*) color='\033[1;34m' ;;
      *) color='\033[0;37m' ;;
    esac
    printf '%b%s\033[0m\n' "$color" "$line"
    sleep 0.65
  done
}

answer() {
  sed -n '15,200p' demo/reviewed-run.txt | while IFS= read -r line; do
    printf '%s\n' "$line"
    sleep 0.38
  done
}

QUESTION="Inspect the actual images of The Japanese Footbridge and Flower Beds in Holland. Compare their edge cropping, depth cues, and directional brushwork, then explain which better supports a quiet contemplative room."

scene
printf '\n\033[1;37m                 POLIGN MULTI-COLLECTION\033[0m\n'
printf '\033[1;36m                   + MULTIMODAL RAG\033[0m\n\n'
printf '       memory  →  scoped retrieval  →  image evidence\n'
printf '                  →  review  →  summary\n\n'
printf '\033[2m       A recorded, reproducible tour in one durable database.\033[0m\n'
sleep 4

scene
.venv/bin/python scripts/demo-visuals.py architecture
sleep 5

scene
narrate "1. Live collection state"
run .venv/bin/polign-curator collections

scene
narrate "2. Curator preferences are durable memory"
run .venv/bin/polign-curator memories --history

scene
.venv/bin/python scripts/demo-visuals.py artworks
sleep 5

scene
narrate "3. Ask a question that requires images and research"
printf '\n\033[1;37m'
printf '%s\n' "$QUESTION" | fold -s -w 96
printf '\033[0m'
sleep 4

printf '\n\033[2m$ polign-curator ask --summary [question above]\033[0m\n\n'
trace
sleep 3

scene
.venv/bin/python scripts/demo-visuals.py review
sleep 5

scene
narrate "4. The reviewed, citation-preserving summary"
answer
sleep 5

scene
narrate "5. Visual observations remain durable and reusable"
run .venv/bin/polign-curator collections

printf '\n\033[1;32m✓ filtered retrieval   ✓ multimodal evidence   ✓ independent review\033[0m\n'
printf '\033[1;32m✓ final summary        ✓ durable visual cache\033[0m\n'
sleep 5
