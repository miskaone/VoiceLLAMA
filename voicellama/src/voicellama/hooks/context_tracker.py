#!/usr/bin/env python3
"""
PostToolUse hook that tracks and estimates context window usage.
Posts updates to VoiceLLAMA avatar server.

Install: Copy to ~/.claude/hooks/
"""
import json
import sys
import os
import time

import requests
from pathlib import Path


VOICELLAMA_URL = "http://localhost:8333/context"
MAX_CONTEXT = 200000
BASE_TOKENS = 21500


def get_state_file() -> Path:
    """Get platform-appropriate state file path."""
    if os.name == 'nt':
        return Path(os.environ.get('TEMP', '.')) / 'voicellama_context_state.json'
    return Path('/tmp/voicellama_context_state.json')


def load_state() -> dict:
    """Load tracking state from file."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    return {"estimated_tokens": 0, "tool_calls": 0, "last_posted": 0, "last_percentage": 0}


def save_state(state: dict):
    """Save tracking state to file."""
    try:
        with open(get_state_file(), "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def estimate_tokens(text: str) -> int:
    """Rough estimate of tokens in text (approx 4 chars per token)."""
    return len(text) // 4


def post_context(percentage: float):
    """Post context percentage to VoiceLLAMA server."""
    try:
        requests.post(VOICELLAMA_URL, json={"percentage": round(percentage, 1)}, timeout=2)
    except requests.RequestException:
        pass


def main():
    try:
        input_data = {}
        try:
            input_data = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass

        state = load_state()

        tool_input = input_data.get("tool_input", {})
        tool_output = input_data.get("tool_output", "")

        input_tokens = estimate_tokens(json.dumps(tool_input))

        if isinstance(tool_output, str):
            output_tokens = estimate_tokens(tool_output)
        else:
            output_tokens = estimate_tokens(json.dumps(tool_output))

        overhead = 100

        state["estimated_tokens"] += input_tokens + output_tokens + overhead
        state["tool_calls"] += 1

        total_tokens = BASE_TOKENS + state["estimated_tokens"]
        percentage = (total_tokens / MAX_CONTEXT) * 100
        percentage = min(percentage, 100)

        now = time.time()
        last_posted = state.get("last_posted", 0)
        last_percentage = state.get("last_percentage", 0)

        should_post = (
            abs(percentage - last_percentage) >= 2 or
            (now - last_posted) >= 30
        )

        if should_post:
            state["last_posted"] = now
            state["last_percentage"] = percentage
            post_context(percentage)

        save_state(state)

        sys.exit(0)

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
