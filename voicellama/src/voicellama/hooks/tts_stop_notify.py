#!/usr/bin/env python3
"""
TTS notification hook for Stop events.
Announces when Claude completes a response/task.

Install: Copy to ~/.claude/hooks/
"""
import json
import sys
import subprocess
import os
import re

import requests
from pathlib import Path


VOICELLAMA_URL = "http://localhost:8333"


def log(msg):
    """Log to temp file for debugging."""
    try:
        log_file = Path('/tmp/voicellama_stop_hook.log')
        if os.name == 'nt':
            log_file = Path(os.environ.get('TEMP', '.')) / 'voicellama_stop_hook.log'
        with open(log_file, 'a') as f:
            f.write(f"{msg}\n")
    except OSError:
        pass


def get_settings():
    """Fetch current TTS settings from API."""
    try:
        response = requests.get(f"{VOICELLAMA_URL}/settings", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return {"chatter_level": "summary", "enabled": True}


def get_last_assistant_message(stop_data: dict) -> str:
    """Extract the last assistant message content from stop data."""
    transcript_path = stop_data.get('transcript_path', '')
    transcript = []

    if transcript_path:
        try:
            with open(transcript_path, 'r') as f:
                # Try JSONL format first (one JSON object per line)
                content = f.read()
                lines = content.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            transcript.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

                # If JSONL parsing got nothing, try as single JSON
                if not transcript:
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            transcript = data
                        elif isinstance(data, dict):
                            transcript = data.get('messages', data.get('transcript', []))
                    except json.JSONDecodeError:
                        pass
        except OSError as e:
            log(f"Error reading transcript: {e}")

    if not transcript:
        transcript = stop_data.get('transcript', [])

    if not transcript:
        return ''

    log(f"Transcript has {len(transcript)} entries")

    # Check for compacted transcript with summary
    for msg in transcript:
        if msg.get('type') == 'summary':
            summary = msg.get('summary', '')
            if summary:
                log(f"Found compacted summary: {summary}")
                return summary

    # Look for assistant messages (standard format)
    for msg in reversed(transcript):
        role = msg.get('role')
        msg_type = msg.get('type')

        # Handle type='assistant' format
        if msg_type == 'assistant':
            message = msg.get('message', {})
            if isinstance(message, dict):
                content = message.get('content', '')
                if isinstance(content, str) and content:
                    return content
                elif isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                    if text_parts:
                        return ' '.join(text_parts)

        # Handle role='assistant' format
        elif role == 'assistant':
            content = msg.get('content', '')
            if isinstance(content, str) and content:
                return content
            elif isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                if text_parts:
                    return ' '.join(text_parts)

    return ''


def extract_summary(stop_data: dict) -> str:
    """Extract a summary announcement from stop data."""
    reason = stop_data.get('stop_reason', '')

    # Get the last assistant message using the proper transcript reader
    last_message = get_last_assistant_message(stop_data)
    log(f"Last message length: {len(last_message)}")

    if not last_message:
        if reason == 'end_turn':
            return "Ready for next request"
        elif reason == 'tool_use':
            return None
        elif reason == 'max_tokens':
            return "Response complete"
        return "Task complete"

    # Clean the message for analysis
    clean_msg = last_message.strip()

    # Try to find a markdown heading as summary
    heading_match = re.search(r'^##?\s+(.+)$', clean_msg, re.MULTILINE)
    if heading_match:
        heading = heading_match.group(1).strip()
        if len(heading) <= 100:
            log(f"Using heading: {heading}")
            return heading

    # Try first non-empty line that's not code
    lines = clean_msg.split('\n')
    for line in lines[:5]:
        line = line.strip()
        # Skip code blocks, empty lines, markdown syntax
        if not line or line.startswith('```') or line.startswith('|') or line.startswith('-'):
            continue
        # Remove markdown formatting
        line = re.sub(r'^#+\s*', '', line)
        line = re.sub(r'\*+([^*]+)\*+', r'\1', line)
        line = re.sub(r'`([^`]+)`', r'\1', line)
        if line and len(line) >= 10:
            if len(line) <= 120:
                log(f"Using first line: {line}")
                return line
            return line[:117] + "..."

    # Fallback: first sentence
    first_sentence = clean_msg.split('.')[0].strip()
    if first_sentence and len(first_sentence) >= 10:
        if len(first_sentence) <= 120:
            return first_sentence
        return first_sentence[:117] + "..."

    return "Task complete"


def main():
    try:
        log("Stop hook triggered")

        input_data = json.load(sys.stdin)
        log(f"Stop data keys: {list(input_data.keys())}")

        stop_reason = input_data.get('stop_reason', '')
        log(f"Stop reason: {stop_reason}")

        if stop_reason == 'tool_use':
            log("Skipping - tool_use stop")
            sys.exit(0)

        settings = get_settings()
        chatter_level = settings.get('chatter_level', 'summary')
        log(f"Chatter level: {chatter_level}")

        if chatter_level == 'verbose':
            text = get_last_assistant_message(input_data)
            message_type = 'detail'
            max_length = 2000
            log(f"Verbose mode - full message length: {len(text)}")
        else:
            text = extract_summary(input_data)
            message_type = 'summary'
            max_length = 150

        if not text:
            log("No text to announce")
            sys.exit(0)

        # Clean up text
        text = text.strip()
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
        text = re.sub(r'_+([^_]+)_+', r'\1', text)
        text = re.sub(r'\n{2,}', '. ', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = text.strip()

        if len(text) > max_length:
            text = text[:max_length - 3] + "..."

        log(f"Announcing ({message_type}): {text[:80]}...")

        # Use announce.py script directly (same directory as this hook)
        announce_script = Path(__file__).parent / 'announce.py'
        subprocess.Popen(
            [sys.executable, str(announce_script), text, message_type],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        sys.exit(0)

    except Exception as e:
        log(f"Stop hook error: {e}")
        sys.exit(0)


if __name__ == '__main__':
    main()
