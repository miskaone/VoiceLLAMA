#!/usr/bin/env python3
"""
Smart TTS announcer that respects chatter level settings.
Usage: python -m voicellama.hooks.announce "text" [message_type]

Message types:
  - question: User questions (sparse, summary, verbose)
  - summary: Task completion summaries (summary, verbose)
  - detail: Detailed narration (verbose only)
"""
import sys
import json

import requests


VOICELLAMA_URL = "http://localhost:8333"


def get_settings():
    """Fetch current TTS settings from API."""
    try:
        response = requests.get(f"{VOICELLAMA_URL}/settings", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return {
        "enabled": True,
        "chatter_level": "sparse",
        "voice": "af_heart",
        "speed": 1.0,
        "custom_states": {
            "question": True,
            "summary": False,
            "detail": False
        }
    }


def should_announce(message_type: str, chatter_level: str, custom_states: dict = None) -> bool:
    """Determine if we should announce based on message type and chatter level."""
    if chatter_level == "custom" and custom_states:
        return custom_states.get(message_type, False)

    if message_type == "question":
        return True
    elif message_type == "summary":
        return chatter_level in ["summary", "verbose"]
    elif message_type == "detail":
        return chatter_level == "verbose"
    return False


def announce(text: str, voice: str = "af_heart", speed: float = 1.0) -> dict:
    """Send text to VoiceLLAMA API for TTS."""
    payload = {
        "text": text,
        "voice": voice,
        "speed": speed
    }

    try:
        response = requests.post(f"{VOICELLAMA_URL}/tts/announce", json=payload, timeout=30)

        if response.status_code == 200:
            return {"status": "success", "text": text}
        else:
            return {"status": "error", "error": response.text}

    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Could not connect to VoiceLLAMA API. Is the server running?"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m voicellama.hooks.announce 'text' [question|summary|detail]")
        sys.exit(1)

    text = sys.argv[1]
    message_type = sys.argv[2] if len(sys.argv) > 2 else "detail"

    settings = get_settings()

    if not settings.get("enabled", True):
        print(json.dumps({"status": "skipped", "reason": "TTS disabled"}))
        sys.exit(0)

    chatter_level = settings.get("chatter_level", "sparse")
    custom_states = settings.get("custom_states", {})

    if not should_announce(message_type, chatter_level, custom_states):
        print(json.dumps({
            "status": "skipped",
            "reason": f"Chatter level '{chatter_level}' does not include '{message_type}'"
        }))
        sys.exit(0)

    voice = settings.get("voice", "af_heart")
    speed = settings.get("speed", 1.0)

    result = announce(text, voice, speed)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
