#!/usr/bin/env bash
# Copyright (c) 2026 Islem Bargaoui
# Licensed under the PolyForm Noncommercial License 1.0.0.
# Commercial use requires separate written permission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="jarvis-feedback-hook-for-codex"
MARKETPLACE_NAME="jarvis-feedback"
DEFAULT_SOURCE="$SCRIPT_DIR"

usage() {
  cat <<'EOF'
JARVIS Feedback Hook for Codex

Usage:
  ./install.sh [--source SOURCE] [--ref REF]

Options:
  --source SOURCE  Marketplace source passed to Codex.
                   Defaults to this local checkout.
                   Examples: IslemBrg/jarvis-feedback-hook-for-codex
                             https://github.com/IslemBrg/jarvis-feedback-hook-for-codex
  --ref REF        Git ref to use when SOURCE is a Git marketplace.
  -h, --help       Show this help.

After installation, manage updates with:
  codex plugin marketplace upgrade
  codex plugin add jarvis-feedback-hook-for-codex --marketplace jarvis-feedback
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

require_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    die "Codex CLI was not found in PATH."
  fi
}

check_say() {
  if ! command -v say >/dev/null 2>&1; then
    echo "Warning: macOS 'say' command was not found. Hooks will install, but speech will not work."
    return
  fi

  if ! say -v "?" | grep -qi "^Jamie\\b"; then
    echo "Warning: macOS voice 'Jamie' was not found."
    echo "List voices with: say -v \"?\""
    echo "Override at runtime with: CODEX_TTS_VOICE=Samantha"
  fi
}

SOURCE="$DEFAULT_SOURCE"
REF=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      [[ $# -ge 2 ]] || die "--source requires a value"
      SOURCE="$2"
      shift 2
      ;;
    --source=*)
      SOURCE="${1#--source=}"
      shift
      ;;
    --ref)
      [[ $# -ge 2 ]] || die "--ref requires a value"
      REF="$2"
      shift 2
      ;;
    --ref=*)
      REF="${1#--ref=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      die "unknown option '$1'"
      ;;
  esac
done

require_codex
check_say

marketplace_args=("$SOURCE")
if [[ -n "$REF" ]]; then
  marketplace_args+=(--ref "$REF")
fi

echo "Adding Codex plugin marketplace: $SOURCE"
codex plugin marketplace add "${marketplace_args[@]}"

echo "Installing plugin: $PLUGIN_NAME"
codex plugin add "$PLUGIN_NAME" --marketplace "$MARKETPLACE_NAME"

echo "Installed JARVIS Feedback Hook for Codex."
echo "Restart Codex if hooks do not fire immediately."
