#!/usr/bin/env bash
# Copyright (c) 2026 Islem Bargaoui
# Licensed under the PolyForm Noncommercial License 1.0.0.
# Commercial use requires separate written permission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-"$HOME/.codex"}"
TTS_DIR="$CODEX_HOME/tts"
HOOKS_FILE="$CODEX_HOME/hooks.json"
SCRIPT_PATH="$TTS_DIR/speak_event.py"
STATE_FILE="$TTS_DIR/jarvis-feedback-hook-state.json"
DEFAULT_VOICE="${CODEX_TTS_VOICE:-Jamie}"

usage() {
  cat <<'EOF'
JARVIS Feedback Hook for Codex

Usage:
  ./configure.sh install [--voice VOICE] [HOOK...]
  ./configure.sh enable [HOOK...]
  ./configure.sh disable [HOOK...]
  ./configure.sh uninstall
  ./configure.sh status
  ./configure.sh voices

Hooks:
  all
  prompt
  stop
  permission
  pre-compact
  post-compact

Examples:
  ./configure.sh install --voice Jamie
  ./configure.sh disable stop
  ./configure.sh enable prompt pre-compact
  ./configure.sh uninstall

Notes:
  "disable" leaves installed files in place and removes only this project's
  managed hook declarations from ~/.codex/hooks.json. JSON has no comments,
  so this is the practical equivalent of commenting out those hook entries.
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

backup_hooks() {
  mkdir -p "$CODEX_HOME"
  if [[ -f "$HOOKS_FILE" ]]; then
    cp "$HOOKS_FILE" "$HOOKS_FILE.bak.$(date +%Y%m%d-%H%M%S)"
  fi
}

install_files() {
  mkdir -p "$TTS_DIR"
  install -m 755 "$SCRIPT_DIR/speak_event.py" "$SCRIPT_PATH"
  python3 -m py_compile "$SCRIPT_PATH"
}

write_state() {
  local voice="$1"
  mkdir -p "$TTS_DIR"
  STATE_FILE="$STATE_FILE" SCRIPT_PATH="$SCRIPT_PATH" VOICE="$voice" python3 - <<'PY'
import json
import os

state_file = os.environ["STATE_FILE"]
state = {}
if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
    except json.JSONDecodeError:
        state = {}

state["script_path"] = os.environ["SCRIPT_PATH"]
state["voice"] = os.environ["VOICE"]

with open(state_file, "w") as f:
    json.dump(state, f, indent=2)
    f.write("\n")
PY
}

check_voice() {
  local voice="$1"
  if ! command -v say >/dev/null 2>&1; then
    echo "Warning: macOS 'say' command was not found."
    return
  fi
  if ! say -v "?" | grep -qi "^$voice\\b"; then
    echo "Warning: macOS voice '$voice' was not found."
    echo "List voices with: say -v \"?\""
    echo "Configure another voice with: ./configure.sh install --voice Samantha"
  fi
}

run_hooks_manager() {
  local action="$1"
  shift || true

  HOOKS_FILE="$HOOKS_FILE" SCRIPT_PATH="$SCRIPT_PATH" STATE_FILE="$STATE_FILE" \
    python3 - "$action" "$@" <<'PY'
import json
import os
import sys

HOOKS = {
    "prompt": {
        "event": "UserPromptSubmit",
        "arg": "prompt",
        "status": "Codex TTS: prompt received",
    },
    "stop": {
        "event": "Stop",
        "arg": "stop",
        "status": "Codex TTS: response complete",
    },
    "permission": {
        "event": "PermissionRequest",
        "arg": "permission",
        "status": "Codex TTS: permission requested",
    },
    "pre-compact": {
        "event": "PreCompact",
        "arg": "pre_compact",
        "status": "Codex TTS: compacting context",
    },
    "post-compact": {
        "event": "PostCompact",
        "arg": "post_compact",
        "status": "Codex TTS: context restored",
    },
}

ALIASES = {
    "all": list(HOOKS),
    "user-prompt": ["prompt"],
    "user_prompt": ["prompt"],
    "userprompt": ["prompt"],
    "prompt": ["prompt"],
    "stop": ["stop"],
    "permission": ["permission"],
    "permission-request": ["permission"],
    "permission_request": ["permission"],
    "precompact": ["pre-compact"],
    "pre_compact": ["pre-compact"],
    "pre-compact": ["pre-compact"],
    "postcompact": ["post-compact"],
    "post_compact": ["post-compact"],
    "post-compact": ["post-compact"],
}


def selected(names):
    if not names:
        return list(HOOKS)
    result = []
    for name in names:
        key = name.strip().lower()
        if key not in ALIASES:
            valid = ", ".join(["all", *HOOKS])
            raise SystemExit(f"Unknown hook '{name}'. Valid hooks: {valid}")
        for hook in ALIASES[key]:
            if hook not in result:
                result.append(hook)
    return result


def load_json(path):
    if not os.path.exists(path):
        return {"hooks": {}}
    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"{path} field 'hooks' must be an object")
    return data


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_state(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def hook_command(script_path, hook):
    return f"{script_path} {HOOKS[hook]['arg']}"


def managed_hook(item, hook):
    if not isinstance(item, dict):
        return False
    if item.get("type") != "command":
        return False
    if item.get("statusMessage") != HOOKS[hook]["status"]:
        return False
    command = item.get("command", "")
    return isinstance(command, str) and command.endswith(f" {HOOKS[hook]['arg']}") and "speak_event.py" in command


def remove_hook(data, hook):
    event = HOOKS[hook]["event"]
    groups = data.get("hooks", {}).get(event, [])
    if not isinstance(groups, list):
        return False

    changed = False
    kept_groups = []
    for group in groups:
        if not isinstance(group, dict):
            kept_groups.append(group)
            continue
        hook_items = group.get("hooks")
        if not isinstance(hook_items, list):
            kept_groups.append(group)
            continue
        kept_items = [item for item in hook_items if not managed_hook(item, hook)]
        if len(kept_items) != len(hook_items):
            changed = True
        if kept_items:
            updated = dict(group)
            updated["hooks"] = kept_items
            kept_groups.append(updated)

    if kept_groups:
        data["hooks"][event] = kept_groups
    elif event in data.get("hooks", {}):
        del data["hooks"][event]
    return changed


def add_hook(data, script_path, hook):
    remove_hook(data, hook)
    event = HOOKS[hook]["event"]
    data.setdefault("hooks", {}).setdefault(event, []).append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": hook_command(script_path, hook),
                    "timeout": 60,
                    "statusMessage": HOOKS[hook]["status"],
                }
            ]
        }
    )


def active_hooks(data):
    active = []
    for hook, spec in HOOKS.items():
        groups = data.get("hooks", {}).get(spec["event"], [])
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for item in group.get("hooks", []):
                if managed_hook(item, hook):
                    active.append(hook)
                    break
    return active


action = sys.argv[1]
names = sys.argv[2:]
hooks_file = os.environ["HOOKS_FILE"]
script_path = os.environ["SCRIPT_PATH"]
state_file = os.environ["STATE_FILE"]

data = load_json(hooks_file)
state = load_state(state_file)
state.setdefault("enabled_hooks", [])

if action == "status":
    active = active_hooks(data)
    print(f"hooks_file: {hooks_file}")
    print(f"script_path: {script_path}")
    print(f"voice: {state.get('voice', 'Jamie')}")
    for hook in HOOKS:
        print(f"{hook}: {'enabled' if hook in active else 'disabled'}")
    raise SystemExit(0)

hooks = selected(names)

if action == "enable":
    for hook in hooks:
        add_hook(data, script_path, hook)
    enabled = active_hooks(data)
    state["enabled_hooks"] = enabled
    save_json(hooks_file, data)
    save_state(state_file, state)
    print("Enabled hooks: " + ", ".join(hooks))
elif action == "disable":
    for hook in hooks:
        remove_hook(data, hook)
    enabled = active_hooks(data)
    state["enabled_hooks"] = enabled
    save_json(hooks_file, data)
    save_state(state_file, state)
    print("Disabled hooks: " + ", ".join(hooks))
elif action == "uninstall":
    for hook in list(HOOKS):
        remove_hook(data, hook)
    state["enabled_hooks"] = []
    save_json(hooks_file, data)
    save_state(state_file, state)
    print("Removed managed hook declarations")
else:
    raise SystemExit(f"Unsupported action: {action}")
PY
}

run_selected_hooks_manager() {
  local action="$1"
  if [[ ${#HOOK_ARGS[@]} -gt 0 ]]; then
    run_hooks_manager "$action" "${HOOK_ARGS[@]}"
  else
    run_hooks_manager "$action"
  fi
}

ACTION="${1:-help}"
shift || true

VOICE="$DEFAULT_VOICE"
HOOK_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --voice)
      [[ $# -ge 2 ]] || die "--voice requires a value"
      VOICE="$2"
      shift 2
      ;;
    --voice=*)
      VOICE="${1#--voice=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      HOOK_ARGS+=("$1")
      shift
      ;;
  esac
done

case "$ACTION" in
  install)
    backup_hooks
    install_files
    write_state "$VOICE"
    run_selected_hooks_manager enable
    python3 -m json.tool "$HOOKS_FILE" >/dev/null
    check_voice "$VOICE"
    echo "Installed JARVIS Feedback Hook for Codex."
    echo "Voice:  $VOICE"
    echo "Script: $SCRIPT_PATH"
    echo "Hooks:  $HOOKS_FILE"
    echo "Restart Codex if hooks do not fire immediately."
    ;;
  enable)
    [[ -f "$SCRIPT_PATH" ]] || install_files
    backup_hooks
    run_selected_hooks_manager enable
    python3 -m json.tool "$HOOKS_FILE" >/dev/null
    echo "Restart Codex if hooks do not fire immediately."
    ;;
  disable)
    backup_hooks
    run_selected_hooks_manager disable
    python3 -m json.tool "$HOOKS_FILE" >/dev/null
    ;;
  uninstall)
    backup_hooks
    run_hooks_manager uninstall
    rm -f "$SCRIPT_PATH" "$STATE_FILE"
    python3 -m json.tool "$HOOKS_FILE" >/dev/null
    echo "Uninstalled JARVIS Feedback Hook for Codex."
    ;;
  status)
    run_hooks_manager status
    ;;
  voices)
    say -v "?"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage
    die "unknown command '$ACTION'"
    ;;
esac
