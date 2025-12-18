#!/usr/bin/env python3
"""
TTS notification hook for tool approvals.
Announces when Claude wants to use tools that need user approval.

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


def build_announcement(tool_name: str, tool_input: dict) -> str:
    """Build announcement text based on tool type."""

    if tool_name == "AskUserQuestion":
        questions = tool_input.get('questions', [])
        if len(questions) == 1:
            return f"Question: {questions[0].get('question', '')}"
        elif len(questions) > 1:
            return f"I have {len(questions)} questions for you."
        return None

    elif tool_name == "Write":
        file_path = tool_input.get('file_path', '')
        filename = Path(file_path).name if file_path else 'file'
        return f"Creating file: {filename}"

    elif tool_name == "Edit":
        file_path = tool_input.get('file_path', '')
        filename = Path(file_path).name if file_path else 'file'
        return f"Editing file: {filename}"

    elif tool_name == "Bash":
        command = tool_input.get('command', '')
        first_cmd = command.split()[0] if command else 'command'
        desc = tool_input.get('description', '')
        if desc:
            return f"{desc}"
        return f"Running: {first_cmd}"

    elif tool_name == "TodoWrite":
        todos = tool_input.get('todos', [])
        completed = [t for t in todos if t.get('status') == 'completed']
        in_progress = [t for t in todos if t.get('status') == 'in_progress']

        if completed:
            last_completed = completed[-1].get('content', 'task')
            return f"Completed: {last_completed}"
        elif in_progress:
            current = in_progress[0].get('activeForm', in_progress[0].get('content', 'task'))
            return f"{current}"
        return None

    elif tool_name == "Notification":
        message = tool_input.get('message', '')
        if message:
            return message
        return None

    else:
        return f"Using tool: {tool_name}"


def get_message_type(tool_name: str) -> str:
    """Determine message type for chatter level filtering."""
    if tool_name == "AskUserQuestion":
        return "question"
    elif tool_name == "TodoWrite":
        return "summary"
    elif tool_name == "Notification":
        return "detail"
    elif tool_name in ["Write", "Edit", "Bash"]:
        return "detail"
    return "detail"


def main():
    try:
        log("Tool hook triggered")

        input_data = json.load(sys.stdin)
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        log(f"Tool: {tool_name}")

        text = build_announcement(tool_name, tool_input)
        if not text:
            sys.exit(0)

        if len(text) > 150:
            text = text[:147] + "..."

        msg_type = get_message_type(tool_name)

        log(f"Announcing ({msg_type}): {text[:50]}...")

        subprocess.Popen(
            [sys.executable, '-m', 'voicellama.hooks.announce', text, msg_type],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        sys.exit(0)

    except Exception as e:
        log(f"Hook error: {e}")
        sys.exit(0)


if __name__ == '__main__':
    main()
