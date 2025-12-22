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
                data = json.load(f)
                if isinstance(data, list):
                    transcript = data
                elif isinstance(data, dict):
                    transcript = data.get('messages', data.get('transcript', []))
        except (OSError, json.JSONDecodeError) as e:
            log(f"Error reading transcript: {e}")

    if not transcript:
        transcript = stop_data.get('transcript', [])

    if not transcript:
        return ''

    for msg in reversed(transcript):
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                if text_parts:
                    return ' '.join(text_parts)
            break

    return ''


def extract_summary(stop_data: dict) -> str:
    """Extract a summary announcement from stop data."""
    reason = stop_data.get('stop_reason', '')
    transcript = stop_data.get('transcript', [])

    last_message = ''
    if transcript:
        for msg in reversed(transcript):
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')
                if isinstance(content, str):
                    last_message = content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            last_message = item.get('text', '')
                            break
                break

    if last_message:
        lower_msg = last_message.lower()

        if any(lower_msg.startswith(word) for word in ['done', 'finished', 'completed', 'i\'ve', 'i have']):
            first_sentence = last_message.split('.')[0]
            if len(first_sentence) <= 100:
                return first_sentence
            return first_sentence[:97] + "..."

        if any(word in lower_msg for word in ['complete', 'finished', 'done', 'implemented', 'added', 'fixed', 'created']):
            lines = last_message.split('\n')
            for line in lines[:3]:
                if line.strip() and len(line) < 100:
                    return line.strip()

    if reason == 'end_turn':
        return "Ready for next request"
    elif reason == 'tool_use':
        return None
    elif reason == 'max_tokens':
        return "Response complete"

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
