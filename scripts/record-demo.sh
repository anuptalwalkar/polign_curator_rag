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

asciinema record --overwrite --window-size 112x32 --idle-time-limit 2 \
  --output-format asciicast-v2 --command ./scripts/demo-session.sh demo.cast
agg --cols 112 --rows 32 --font-size 16 --idle-time-limit 2 demo.cast demo.gif

echo "wrote demo.cast and demo.gif"
