# app/utils.py
import os
import json
from typing import Any

def load_env(name: str, default: Any = None):
    return os.getenv(name, default)

def summarize_event(event: dict) -> str:
    # simple summary generator
    return f"{event.get('source')} - {event.get('message', '')} - ip={event.get('ip')}"
