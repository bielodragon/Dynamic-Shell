#!/usr/bin/env python3
"""Hook de observação do Claude Code: lê contexto JSON e não interfere em decisões."""
import hashlib
import json
import sys
from pathlib import Path

from activity_cli import request


def map_event(payload):
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        return None
    identity = session + ":" + str(payload.get("agent_id", "main"))
    activity_id = "claude:" + hashlib.sha256(identity.encode()).hexdigest()[:24]
    event = payload.get("hook_event_name")
    if event == "SessionEnd":
        return ("remove", activity_id)
    states = {
        "SessionStart": ("paused", "Claude pronto", 8),
        "UserPromptSubmit": ("running", "Claude trabalhando", 3600),
        "PreToolUse": ("running", "Claude trabalhando", 3600),
        "PostToolUse": ("running", "Claude trabalhando", 3600),
        "PermissionRequest": ("waiting", "Claude aguarda você", 3600),
        "Stop": ("success", "Claude respondeu", 8),
        "StopFailure": ("error", "Claude: erro na resposta", 15),
    }
    if event == "Notification":
        state = {"permission_prompt": ("waiting", "Claude aguarda você", 3600),
                 "idle_prompt": ("paused", "Claude aguarda mensagem", 30)}.get(payload.get("notification_type"))
    else:
        state = states.get(event)
    if not state:
        return None
    project = Path(str(payload.get("cwd", ""))).name[:70]
    tool = str(payload.get("tool_name", ""))[:70] if event == "PreToolUse" else ""
    return ("update", {
        "id": activity_id, "app": "Claude Code", "title": state[1], "state": state[0],
        "detail": ("Ferramenta: " + tool) if tool else project,
        "progress": None, "ttl": state[2],
    })


def main():
    # A ausência da ilha não deve impedir o trabalho do aplicativo.
    try:
        raw = sys.stdin.read(1_048_577)
        if len(raw) > 1_048_576:
            return
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return
        mapped = map_event(payload)
        if mapped:
            request(*mapped)
    except Exception:
        pass


if __name__ == "__main__":
    main()
