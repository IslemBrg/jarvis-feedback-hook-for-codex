# JARVIS Feedback Hook for Codex

Lightweight macOS text-to-speech feedback hooks for Codex CLI.

Copyright (c) 2026 Islem Bargaoui.

This project makes Codex feel a little more alive. It uses Codex hooks plus macOS `say` to speak short status cues when conversation events happen.

## What It Does

The hook script speaks on these Codex events:

- `UserPromptSubmit`: when you submit a prompt.
- `Stop`: when Codex finishes a turn.
- `PermissionRequest`: when Codex needs approval.
- `PreCompact`: before context compaction.
- `PostCompact`: after context compaction.

For `Stop`, the script tries to read Codex's transcript and speak a short, useful phrase from the final assistant response. If the response is long, noisy, contains code, contains URLs, or would take too long to say, it falls back to a randomized completion phrase.

Example final response:

```text
Done, sir.

I wired the Stop hook so it now behaves conditionally...
```

Spoken output:

```text
Done, sir. I wired the Stop hook so it now behaves conditionally
```

## Why This Exists

Let's be real: long context windows and deep thinking passes take time. When you trigger Codex on a massive task, you don't just sit there staring at a terminal, you alt-tab into a browser, check Slack, or grab a coffee.

By the time you look back, your agent has been sitting there for 10 minutes doing absolutely nothing because it hit a **Permission Gate** and is quietly waiting for you to type `yes`.

**The JARVIS Feedback Hook** solves this context-switching decay. By translating silent log states into real-time audio telemetry, you know exactly when the system requires your authorization, when it's compacting memory, or when it has completed the objective.

## Requirements

- macOS
- Python 3
- Codex CLI with hook support
- The built-in macOS `say` command
- An installed macOS voice, such as `Jamie`

List installed voices:

```bash
say -v "?"
```

## Configure

Clone or download this repo, then run:

```bash
./configure.sh install
```

The configurator can install, uninstall, enable, disable, and manage individual hook events from one script.

Install will:

- copy `speak_event.py` to `~/.codex/tts/speak_event.py`
- make it executable
- back up any existing `~/.codex/hooks.json`
- merge this project's hook declarations into `~/.codex/hooks.json`
- validate the Python script and hook JSON

Restart Codex if hooks do not fire immediately.

## Manage Hooks

```bash
./configure.sh status
./configure.sh disable
./configure.sh enable
./configure.sh uninstall
```

`disable` does not remove installed files. It removes this project's managed hook declarations from the active Codex config, which is the JSON-safe equivalent of commenting them out.

`uninstall` removes this project's hook declarations and deletes the installed script/state files from `~/.codex/tts`.

You can manage each hook independently:

```bash
./configure.sh disable stop
./configure.sh enable stop
./configure.sh disable prompt pre-compact
./configure.sh enable permission post-compact
```

Supported hook names:

- `prompt`
- `stop`
- `permission`
- `pre-compact`
- `post-compact`
- `all`

## Choose A Voice

The default voice is `Jamie`.

To install with another voice:

```bash
./configure.sh install --voice Samantha
```

At runtime, the script also reads `CODEX_TTS_VOICE`, so you can change the voice from the environment if your Codex launch setup preserves it.

List available voices:

```bash
./configure.sh voices
```

## Manual Install

```bash
mkdir -p ~/.codex/tts
cp speak_event.py ~/.codex/tts/speak_event.py
chmod +x ~/.codex/tts/speak_event.py
```

Then copy `hooks.template.json` to:

```text
~/.codex/hooks.json
```

Replace `__SCRIPT_PATH__` with the absolute path to the script, for example:

```text
/Users/YOUR_USER/.codex/tts/speak_event.py
```

## How The Stop Hook Works

When Codex finishes a turn, the script:

1. Reads the hook payload from `stdin`.
2. Looks for a transcript path and turn id.
3. Extracts the latest assistant message for that turn.
4. Cleans markdown, links, code, file paths, and citations.
5. Speaks the full message only if it is short.
6. Otherwise extracts the first useful lead phrase.
7. Falls back to a random completion phrase if extraction is not safe.

Current speech budget:

- `MAX_SAYABLE_CHARS = 180`
- `MAX_SAYABLE_WORDS = 24`

## Avoiding Voice Overlap

Before speaking, the script runs:

```bash
pkill -x say
```

That prevents multiple hook events from talking over each other. The tradeoff is that it stops any currently running macOS `say` process, not only this hook's process.

## Testing

Syntax check:

```bash
python3 -m py_compile speak_event.py
```

Dry run without speaking:

```bash
CODEX_TTS_DRY_RUN=1 ./speak_event.py stop
```

Hook logs are written to:

```text
/tmp/codex_tts_hook.log
```

Override the log path:

```bash
CODEX_TTS_HOOK_LOG=/tmp/my_codex_tts.log ./speak_event.py prompt
```

## Notes

This is intentionally small and local. No background server, no model downloads, no network calls, no package install.

If you already have a custom `~/.codex/hooks.json`, the configurator preserves unrelated hook entries and backs up the file before changes.

## License

This project is source-available under the PolyForm Noncommercial License 1.0.0.

You may use, copy, modify, and share it for noncommercial purposes under the license terms. Commercial use, resale, paid distribution, marketplace packaging, SaaS bundling, or inclusion in a commercial product requires separate written permission from Islem Bargaoui.

See [LICENSE](LICENSE), [NOTICE](NOTICE), and [COMMERCIAL.md](COMMERCIAL.md).
