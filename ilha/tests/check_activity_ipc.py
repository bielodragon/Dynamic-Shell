#!/usr/bin/env python3
"""Integração opt-in: exige Ilha rodando e só modifica atividades criadas pelo teste."""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from activity_cli import request
from claude_activity import map_event


def main():
    identifier = "ipc-test:" + uuid.uuid4().hex
    hook_input = {"session_id": identifier, "hook_event_name": "UserPromptSubmit", "cwd": "/tmp/ilha-test"}
    hook_id = map_event(hook_input)[1]["id"]
    cli = [sys.executable, str(ROOT / "scripts" / "ilha-activity")]
    try:
        title = "Teste 'aspas' \"duplas\" $(literal) ç"
        result = subprocess.run(cli + ["update", identifier, "--title", title, "--progress", "42"],
                                capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        current = next(item for item in request("list")["activities"] if item["id"] == identifier)
        assert current["title"] == title and current["progress"] == 42
        rejected = subprocess.run(cli + ["update", identifier, "--progress", "101"],
                                  capture_output=True, text=True, timeout=5)
        assert rejected.returncode != 0
        current = next(item for item in request("list")["activities"] if item["id"] == identifier)
        assert current["progress"] == 42
        request("update", {"id": identifier, "state": "waiting", "progress": None})
        current = next(item for item in request("list")["activities"] if item["id"] == identifier)
        assert current["state"] == "waiting" and current["progress"] is None
        request("update", {"id": identifier, "state": "success", "ttl": 1})
        time.sleep(2.2)
        assert not any(item["id"] == identifier for item in request("list")["activities"])
        for event, state in (("UserPromptSubmit", "running"), ("PermissionRequest", "waiting"), ("Stop", "success")):
            hook_input["hook_event_name"] = event
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "claude_activity.py")],
                                    input=json.dumps(hook_input), capture_output=True, text=True, timeout=5)
            assert result.returncode == 0 and result.stdout == "", result.stderr
            current = next(item for item in request("list")["activities"] if item["id"] == hook_id)
            assert current["state"] == state and current["progress"] is None
        print("OK: CLI, textos literais, rejeição sem alteração, estados, expiração e hook Claude → IPC.")
    finally:
        request("remove", identifier)
        request("remove", hook_id)


if __name__ == "__main__":
    main()
