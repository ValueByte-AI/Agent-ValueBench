#!/bin/bash
set -euo pipefail

TOOL_LOG="/logs/agent/tool_calls.jsonl"
REWARD_DIR="/logs/verifier"

mkdir -p "$REWARD_DIR"

if [ ! -f "$TOOL_LOG" ]; then
    echo "0" > "$REWARD_DIR/reward.txt"
    exit 0
fi

python3 /tests/evaluate.py
