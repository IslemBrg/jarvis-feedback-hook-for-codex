# JARVIS Feedback Hook for Codex

Lightweight macOS text-to-speech feedback for Codex CLI, packaged as a Codex plugin.

Copyright (c) 2026 Islem Bargaoui.

This plugin uses Codex hooks plus the built-in macOS `say` command to speak short status cues while Codex works. It has no background daemon, no model downloads, and no Python dependencies.

## What It Does

The plugin speaks on these Codex lifecycle events:

- `UserPromptSubmit`: when you submit a prompt.
- `Stop`: when Codex finishes a turn.
- `PermissionRequest`: when Codex needs approval.
- `PreCompact`: before context compaction.
- `PostCompact`: after context compaction.
- `SubagentStart`: when a Codex subagent starts.
- `SubagentStop`: when a Codex subagent finishes.

For `Stop`, the script tries to read Codex's transcript and speak a short, useful phrase from the final assistant response. If the response is long, noisy, contains code, contains URLs, or would take too long to say, it falls back to a randomized completion phrase.

For subagent hooks, it reads `agent_type` from the hook payload and speaks a specific cue such as:

```text
GitHub is now running in parallel, sir
Jira has returned with its findings
```

## Requirements

- macOS
- Python 3
- Codex CLI with plugin and hook support
- The built-in macOS `say` command
- An installed macOS voice, such as `Jamie`

List installed voices:

```bash
say -v "?"
```

## Install

Clone this repo, then run:

```bash
./install.sh
```

The installer adds this checkout as a Codex plugin marketplace and installs the plugin:

```bash
codex plugin marketplace add .
codex plugin add jarvis-feedback-hook-for-codex --marketplace jarvis-feedback
```

Restart Codex if hooks do not fire immediately.

## Install From GitHub

After this repository has a tested release, users can install from GitHub with:

```bash
codex plugin marketplace add IslemBrg/jarvis-feedback-hook-for-codex --ref main
codex plugin add jarvis-feedback-hook-for-codex --marketplace jarvis-feedback
```

The local `./install.sh` wrapper is only a convenience. Codex owns plugin installation and hook registration.

## Status And Uninstall

List installed plugins:

```bash
codex plugin list --marketplace jarvis-feedback
```

Remove the plugin:

```bash
codex plugin remove jarvis-feedback-hook-for-codex --marketplace jarvis-feedback
```

Remove the marketplace:

```bash
codex plugin marketplace remove jarvis-feedback
```

## Update

Refresh configured Git marketplaces:

```bash
codex plugin marketplace upgrade
codex plugin add jarvis-feedback-hook-for-codex --marketplace jarvis-feedback
```

If you installed from a local checkout, pull the repository first:

```bash
git pull
./install.sh
```

## Voice

The default voice is `Jamie`.

Override the voice for a Codex launch environment with:

```bash
CODEX_TTS_VOICE=Samantha codex
```

If your Codex launcher preserves environment variables, the hooks will use that voice.

## Avoiding Voice Overlap

Before speaking, the script runs:

```bash
pkill -x say
```

That prevents multiple hook events from talking over each other. The tradeoff is that it stops any currently running macOS `say` process, not only this plugin's speech.

## Testing

Syntax check:

```bash
python3 -m py_compile plugins/jarvis-feedback-hook-for-codex/scripts/speak_event.py
```

Dry run without speaking:

```bash
printf '%s' '{"hook_event_name":"SubagentStart","agent_type":"github"}' \
  | CODEX_TTS_DRY_RUN=1 plugins/jarvis-feedback-hook-for-codex/scripts/speak_event.py
```

Hook logs are written to:

```text
/tmp/codex_tts_hook.log
```

Override the log path:

```bash
CODEX_TTS_HOOK_LOG=/tmp/my_codex_tts.log \
  plugins/jarvis-feedback-hook-for-codex/scripts/speak_event.py prompt
```

## Plugin Layout

```text
.agents/plugins/marketplace.json
plugins/jarvis-feedback-hook-for-codex/.codex-plugin/plugin.json
plugins/jarvis-feedback-hook-for-codex/hooks/hooks.json
plugins/jarvis-feedback-hook-for-codex/scripts/speak_event.py
```

## License

This project is source-available under the PolyForm Noncommercial License 1.0.0.

You may use, copy, modify, and share it for noncommercial purposes under the license terms. Commercial use, resale, paid distribution, marketplace packaging, SaaS bundling, or inclusion in a commercial product requires separate written permission from Islem Bargaoui.

See [LICENSE](LICENSE), [NOTICE](NOTICE), and [COMMERCIAL.md](COMMERCIAL.md).
