# JARVIS Feedback Hook

macOS speech feedback for Codex lifecycle hooks.

This plugin speaks short status cues for prompt submission, response completion, permission requests, context compaction, and subagent lifecycle events. It uses the built-in macOS `say` command and does not run a daemon.

When an app is using a microphone input, JARVIS speaks at `0.05` volume. The hook renders the same `say` voice to a temporary file, then plays it with macOS `afplay`. Only JARVIS speech is lowered. Microphone use is an estimate of meeting activity; set `CODEX_TTS_MEETING_MODE=always` or `never` when you need to override it. The default is `auto`.

For permission requests, it speaks Codex's short approval reason when provided, without adding a prefix or "sir". If no sayable reason is available, it says "Permission requested".

The default voice is `Jamie`. You can override it by launching Codex with:

```bash
CODEX_TTS_VOICE=Samantha codex
```

Hook logs are written to:

```text
/tmp/codex_tts_hook.log
```

This plugin is licensed under the PolyForm Noncommercial License 1.0.0. Commercial use requires separate written permission.
