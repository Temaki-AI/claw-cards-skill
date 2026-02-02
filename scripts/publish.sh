#!/usr/bin/env bash
# 🦞 Claw Cards — Publish Script (thin wrapper around Python)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${AGENT_WORKSPACE:-$HOME}"
exec python3 "$SCRIPT_DIR/publish.py" "$WORKSPACE"
