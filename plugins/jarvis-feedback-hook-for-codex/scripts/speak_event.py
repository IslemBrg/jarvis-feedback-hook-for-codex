#!/usr/bin/env python3
# Copyright (c) 2026 Islem Bargaoui
# Licensed under the PolyForm Noncommercial License 1.0.0.
# Commercial use requires separate written permission.

import json
import os
import random
import re
import subprocess
import sys
import time

HOOK_LOG = os.environ.get("CODEX_TTS_HOOK_LOG", "/tmp/codex_tts_hook.log")
STATE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "jarvis-feedback-hook-state.json",
)


def configured_voice():
    if os.environ.get("CODEX_TTS_VOICE"):
        return os.environ["CODEX_TTS_VOICE"]
    try:
        with open(STATE_FILE) as state_file:
            state = json.load(state_file)
    except (OSError, json.JSONDecodeError):
        state = {}
    return state.get("voice", "Jamie")


VOICE = configured_voice()
MAX_SAYABLE_CHARS = 180
MAX_SAYABLE_WORDS = 24
SHORT_LEAD_WORDS = 4
DANGLING_ENDINGS = {
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "to",
    "with",
}

PROMPT_PHRASES = [
    "Right away",
    "Of course",
    "On it now",
    "I've got it",
    "Leave it with me",
    "Already moving",
    "Consider me engaged",
    "Understood",
    "Certainly",
    "I'll take it from here",
    "One moment",
    "Let me have a look",
    "I'll sort that out",
    "Processing the thought",
    "Working through it now",
    "A sensible request",
    "I'll pretend that was the plan all along",
    "Routing attention to it",
    "Very good",
    "Let's see what the universe has broken this time",
]

STOP_PHRASES = [
    "All set",
    "That's handled",
    "I've finished that",
    "Response delivered",
    "The work is complete",
    "That should do it",
    "I've wrapped it up",
    "Nothing further from this thread",
    "Systems are nominal",
    "Diagnostics complete",
    "I believe that is the shape of it",
    "The loose ends have been tied off",
    "Objective handled",
    "I've put that in order",
    "Clean finish",
    "That concludes the pass",
    "I've taken care of it",
    "The requested work is done",
    "Standing by for the next questionable idea",
    "Done, with only minimal offense to physics",
]

PERMISSION_PHRASES = [
    "I need your approval before I proceed",
    "Permission required before the next step",
    "This one needs authorization",
    "I'll pause here for your confirmation",
    "I need clearance for that action",
    "Your confirmation is required",
    "I cannot proceed without approval",
    "This requires your explicit say-so",
    "I'm waiting on permission",
    "Approval gate reached",
    "A decision from you is needed",
    "This action needs your consent",
    "I'll need you to authorize this",
    "The system is asking for permission",
    "Confirmation required before continuing",
]

PRE_COMPACT_PHRASES = [
    "Condensing context before we continue",
    "Compressing the working memory",
    "Tidying the cognitive workspace",
    "Archiving the relevant state",
    "Reducing context without losing the plot",
    "Packing the important details",
    "Preparing a memory compression pass",
    "Context is getting dense; recalibrating",
    "Consolidating the thread state",
    "Trimming the conversation payload",
    "Compressing memory before proceeding",
    "Preserving the useful bits",
    "Preparing context compaction",
    "Organizing the accumulated evidence",
    "Making room in the thought buffer",
]

POST_COMPACT_PHRASES = [
    "Context restored",
    "Memory recalibrated",
    "Compaction complete",
    "Working state recovered",
    "The thread has been condensed",
    "Relevant context is back online",
    "Compression pass complete",
    "Memory state stabilized",
    "Context has been repacked",
    "Continuity restored",
    "The useful details survived",
    "Cognitive workspace refreshed",
    "Thread state consolidated",
    "Context pressure relieved",
    "Ready to continue from the compressed state",
]

SUBAGENT_START_PHRASES = [
    "{agent} subagent is online",
    "{agent} subagent initiated",
    "{agent} is taking a parallel look",
    "{agent} is now examining the problem",
    "{agent} has joined the analysis",
    "{agent} is spinning up a separate thread",
    "{agent} is handling the side channel",
    "{agent} is now running in parallel",
    "{agent} is taking that thread",
    "{agent} has been brought into the loop",
]

SUBAGENT_STOP_PHRASES = [
    "{agent} subagent has finished",
    "{agent} has returned with its findings",
    "{agent} parallel pass is complete",
    "{agent} has concluded its thread",
    "{agent} is done with the side analysis",
    "{agent} has handed back the result",
    "{agent} has completed its pass",
    "{agent} thread has settled",
    "{agent} has wrapped its work",
    "{agent} is back from the parallel lane",
]

PHRASES = {
    "prompt": PROMPT_PHRASES,
    "stop": STOP_PHRASES,
    "permission": PERMISSION_PHRASES,
    "pre_compact": PRE_COMPACT_PHRASES,
    "post_compact": POST_COMPACT_PHRASES,
    "subagent_start": SUBAGENT_START_PHRASES,
    "subagent_stop": SUBAGENT_STOP_PHRASES,
}

EVENT_ALIASES = {
    "UserPromptSubmit": "prompt",
    "Stop": "stop",
    "PermissionRequest": "permission",
    "PreCompact": "pre_compact",
    "PostCompact": "post_compact",
    "SubagentStart": "subagent_start",
    "SubagentStop": "subagent_stop",
}

AGENT_TYPE_NAMES = {
    "github": "GitHub",
    "github-agent": "GitHub Agent",
    "git-hub": "GitHub",
    "commit-agent": "Commit Agent",
    "fast-execution-coder": "Fast Execution Coder",
    "jira": "Jira",
    "jira-agent": "Jira",
    "review": "review",
    "reviewer": "review",
    "systems-architect": "Systems Architect",
}

PROPER_SPEECH_STARTS = {
    "API",
    "CLI",
    "DB",
    "GitHub",
    "GQL",
    "Jira",
    "MCP",
    "PR",
    "QA",
    "UI",
    "UX",
}


def log_hook(message):
    try:
        with open(HOOK_LOG, "a") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except Exception:
        pass


def speak(text):
    if os.environ.get("CODEX_TTS_DRY_RUN") == "1":
        log_hook(f"dry_run text={text!r}")
        return

    subprocess.run(
        ["pkill", "-x", "say"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    subprocess.Popen(
        ["say", "-v", VOICE, text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def apply_sir_style(text):
    style = random.choices(
        ["end", "start", "none"],
        weights=[50, 40, 10],
        k=1,
    )[0]
    if style == "start":
        words = re.findall(r"[A-Za-z][A-Za-z0-9]*", text)
        preserve_initial = (
            len(words) >= 2 and words[0][:1].isupper() and words[1][:1].isupper()
        ) or (
            words
            and (
                words[0] in PROPER_SPEECH_STARTS
                or any(char.isupper() for char in words[0][1:])
            )
        )
        if preserve_initial:
            return f"Sir, {text}"
        return f"Sir, {text[:1].lower()}{text[1:]}"
    if style == "end":
        return f"{text}, sir"
    return text


def normalize_event(value):
    if not value:
        return "prompt"
    return EVENT_ALIASES.get(value, value)


def find_first_string(value, keys):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str):
                return item
            found = find_first_string(item, keys)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_first_string(item, keys)
            if found:
                return found
    return None


def is_subagent_payload(value):
    if isinstance(value, dict):
        if find_first_string(value, {"agent_id", "agentId", "agent_type", "agentType"}):
            return True
        if value.get("is_subagent") is True or value.get("isSubagent") is True:
            return True
        for item in value.values():
            if is_subagent_payload(item):
                return True
    elif isinstance(value, list):
        return any(is_subagent_payload(item) for item in value)
    return False


def humanize_agent_type(agent_type):
    if not agent_type:
        return "The subagent"

    normalized = agent_type.strip()
    if not normalized:
        return "The subagent"

    key = normalized.lower()
    if key in AGENT_TYPE_NAMES:
        return AGENT_TYPE_NAMES[key]

    words = re.split(r"[_\-\s]+", normalized)
    acronyms = {"api", "cli", "db", "gql", "mcp", "pr", "qa", "ui", "ux"}
    readable = []
    for word in words:
        if not word:
            continue
        lower = word.lower()
        if lower in acronyms:
            readable.append(lower.upper())
        else:
            readable.append(lower.capitalize())

    return " ".join(readable) or "The subagent"


def subagent_phrase(event, hook_payload):
    agent_type = find_first_string(hook_payload, {"agent_type", "agentType"})
    agent = humanize_agent_type(agent_type)
    template = random.choice(PHRASES[event])
    phrase = template.format(agent=agent)
    log_hook(f"subagent agent_type={agent_type!r} agent={agent!r}")
    return apply_sir_style(phrase)


def find_transcript_path(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"transcript_path", "transcriptPath"} and isinstance(item, str):
                return item
            found = find_transcript_path(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_transcript_path(item)
            if found:
                return found
    return None


def find_turn_id(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"turn_id", "turnId"} and isinstance(item, str):
                return item
            found = find_turn_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_turn_id(item)
            if found:
                return found
    return None


def content_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"output_text", "text"} and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts).strip()


def latest_assistant_message(transcript_path, turn_id=None):
    if not transcript_path or not os.path.exists(transcript_path):
        return None

    latest = None
    in_target_turn = turn_id is None
    try:
        with open(transcript_path) as transcript:
            for line in transcript:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                payload = record.get("payload")
                if record.get("type") == "turn_context" and isinstance(payload, dict):
                    in_target_turn = turn_id is None or payload.get("turn_id") == turn_id
                    if in_target_turn:
                        latest = None
                    continue

                if not in_target_turn:
                    continue

                if record.get("type") == "response_item" and isinstance(payload, dict):
                    if payload.get("type") == "message" and payload.get("role") == "assistant":
                        text = content_text(payload.get("content"))
                        if text:
                            latest = text
                    continue

                if record.get("type") == "event_msg" and isinstance(payload, dict):
                    text = payload.get("last_agent_message")
                    if payload.get("type") == "task_complete" and isinstance(text, str):
                        latest = text
    except OSError:
        return None

    return latest


def clean_for_speech(text):
    text = text.split("<oai-mem-citation>", 1)[0].strip()
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(
        r"(?<!\w)/(?:[^\s`'\"\)\]]+)",
        lambda match: os.path.basename(match.group(0).rstrip(".,;:")),
        text,
    )
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def within_speech_budget(text):
    cleaned = clean_for_speech(text)
    if len(cleaned) > MAX_SAYABLE_CHARS:
        return False
    return len(cleaned.split()) <= MAX_SAYABLE_WORDS


def is_sayable(text):
    if not text:
        return False
    if "```" in text or "<oai-mem-citation>" in text:
        return False
    if "http://" in text or "https://" in text:
        return False
    if text.count("\n") > 1:
        return False

    cleaned = clean_for_speech(text)
    if not within_speech_budget(cleaned):
        return False
    return bool(re.search(r"[A-Za-z0-9]", cleaned))


def plain_paragraphs(text):
    text = text.split("<oai-mem-citation>", 1)[0]
    text = re.sub(r"```.*?```", "\n\n", text, flags=re.DOTALL)

    paragraphs = []
    for block in re.split(r"\n\s*\n+", text):
        lines = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^(?:[-*+]|\d+[.)])\s+", stripped):
                continue
            lines.append(stripped)

        if not lines:
            continue

        paragraph = clean_for_speech(" ".join(lines)).rstrip(":;")
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def sentence_chunks(text):
    protected = re.sub(
        r"\b([A-Za-z0-9_-]+)\.(py|json|toml|md|txt|js|ts|tsx|jsx)\b",
        r"\1§\2",
        text,
    )
    chunks = re.findall(r"[^.!?]+[.!?]?", protected)
    return [
        clean_for_speech(chunk.replace("§", ".")).rstrip(":;")
        for chunk in chunks
        if chunk.strip()
    ]


def first_clause_under_budget(text):
    clauses = re.split(r"\s*(?:;|:|, but\b|, and\b| - | -- )\s*", text)
    if not clauses:
        return None

    clause = clean_for_speech(clauses[0]).rstrip(":;")
    if len(clause.split()) >= 2 and is_sayable(clause):
        return clause
    return None


def has_dangling_ending(text):
    words = re.findall(r"[A-Za-z]+", text.lower())
    return bool(words and words[-1] in DANGLING_ENDINGS)


def extract_speakable_lead(text):
    sentences = []
    for paragraph in plain_paragraphs(text):
        sentences.extend(sentence_chunks(paragraph))
        if len(sentences) >= 3:
            break

    if not sentences:
        return None

    lead = sentences[0]
    if len(lead.split()) <= SHORT_LEAD_WORDS and len(sentences) > 1:
        candidate = f"{lead} {sentences[1]}"
        if is_sayable(candidate) and not has_dangling_ending(candidate):
            return candidate

    if is_sayable(lead):
        return lead

    return first_clause_under_budget(sentences[0])


def stop_phrase_from_transcript(hook_payload):
    transcript_path = find_transcript_path(hook_payload)
    turn_id = find_turn_id(hook_payload)
    message = latest_assistant_message(transcript_path, turn_id)
    if not message:
        log_hook("transcript_missing_or_empty")
        return None
    if not is_sayable(message):
        lead = extract_speakable_lead(message)
        if lead:
            log_hook(f"transcript_lead phrase={lead!r}")
            return lead

        log_hook("transcript_not_sayable")
        return None

    phrase = clean_for_speech(message)
    log_hook(f"transcript_sayable phrase={phrase!r}")
    return phrase


def phrase_for_event(event, hook_payload):
    event = normalize_event(event)

    if event == "stop":
        transcript_phrase = stop_phrase_from_transcript(hook_payload)
        if transcript_phrase:
            return transcript_phrase

    if event in {"subagent_start", "subagent_stop"}:
        return subagent_phrase(event, hook_payload)

    options = PHRASES.get(event, PROMPT_PHRASES)
    phrase = random.choice(options) if isinstance(options, list) else options
    return apply_sir_style(phrase)


def main():
    # Drain hook input so Codex can pass any event payload without blocking on stdin.
    try:
        hook_payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        hook_payload = {}

    payload_event = hook_payload.get("hook_event_name") if isinstance(hook_payload, dict) else None
    event = normalize_event(sys.argv[1] if len(sys.argv) > 1 else payload_event or "prompt")
    if event == "prompt" and is_subagent_payload(hook_payload):
        log_hook("skipped_subagent_prompt")
        return

    phrase = phrase_for_event(event, hook_payload)

    try:
        log_hook(f"event={event} phrase={phrase!r}")
        speak(phrase)
        log_hook(f"spoken voice={VOICE!r}")
    except Exception:
        log_hook("failed")
        return


if __name__ == "__main__":
    main()
