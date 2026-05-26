# JARVIS Feedback Hook

macOS speech feedback for Codex lifecycle hooks.

This plugin speaks short status cues for prompt submission, response completion, permission requests, context compaction, and subagent lifecycle events. It uses the built-in macOS `say` command and does not run a daemon.

The default voice is `Jamie`. You can override it by launching Codex with:

```bash
CODEX_TTS_VOICE=Samantha codex
```

Hook logs are written to:

```text
/tmp/codex_tts_hook.log
```

This plugin is licensed under the PolyForm Noncommercial License 1.0.0. Commercial use requires separate written permission.
