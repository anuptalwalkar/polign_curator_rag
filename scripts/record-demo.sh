#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

if ! command -v asciinema >/dev/null 2>&1; then
  echo "asciinema is required"
  exit 1
fi
if ! command -v agg >/dev/null 2>&1; then
  echo "agg is required"
  exit 1
fi
if ! curl -sf http://127.0.0.1:24400/healthz >/dev/null; then
  echo "start polign-server on 127.0.0.1:24400 first"
  exit 1
fi

asciinema record --overwrite --window-size 112x34 --idle-time-limit 4 \
  --output-format asciicast-v2 --command ./scripts/demo-session.sh demo.cast
agg --cols 112 --rows 34 --font-size 16 --speed 0.85 --idle-time-limit 4 \
  --last-frame-duration 5 demo.cast demo.gif

echo "wrote demo.cast and demo.gif"
