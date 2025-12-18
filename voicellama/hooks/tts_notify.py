#!/usr/bin/env python3
"""
TTS notification hook for AskUserQuestion tool.
Speaks the question(s) when Claude needs user input.

Install: Copy to ~/.claude/hooks/
"""
import json
import sys
import subprocess
import os
from pathlib import Path


def log(msg):
    """Log to temp file for debugging."""
    try:
        log_file = Path('/tmp/voicellama_hook.log')
        if os.name == 'nt':
            log_file = Path(os.environ.get('TEMP', '.')) / 'voicellama_hook.log'
        with open(log_file, 'a') as f:
            f.write(f"{msg}\n")
    except OSError:
        pass


def main():
    try:
        log("Hook triggered")
        input_data = json.load(sys.stdin)
        log(f"Input: {input_data}")

        tool_input = input_data.get('tool_input', {})
        questions = tool_input.get('questions', [])

        if not questions:
            sys.exit(0)

        if len(questions) == 1:
            text = f"Question: {questions[0].get('question', '')}"
        else:
            text = "I have questions for you."

        if len(text) > 100:
            text = text[:100]

        log(f"Announcing: {text}")

        # Use voicellama.hooks.announce module
        subprocess.Popen(
            [sys.executable, '-m', 'voicellama.hooks.announce', text, 'question'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        log("Popen launched")

        sys.exit(0)

    except Exception as e:
        print(f"TTS hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
