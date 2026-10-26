"""Valida tradução de hooks sem chamar serviços reais nem enviar prompts."""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("claude_activity", SCRIPTS / "claude_activity.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class ClaudeActivityTests(unittest.TestCase):
    def test_turn_states_keep_id_without_exposing_prompt(self):
        base = {"session_id": "abc/with spaces", "cwd": "/tmp/projeto",
                "prompt": "conteúdo privado", "tool_input": {"command": "segredo"}}
        start = hook.map_event(dict(base, hook_event_name="UserPromptSubmit"))[1]
        end = hook.map_event(dict(base, hook_event_name="Stop"))[1]
        self.assertEqual(start["id"], end["id"])
        self.assertEqual(start["state"], "running")
        self.assertEqual(end["state"], "success")
        self.assertIsNone(start["progress"])
        self.assertNotIn("conteúdo privado", str(start))
        self.assertNotIn("segredo", str(start))
        self.assertEqual(hook.map_event(dict(base, hook_event_name="SessionEnd")), ("remove", start["id"]))

    def test_permissions_and_unknown_events(self):
        base = {"session_id": "test", "hook_event_name": "Notification"}
        self.assertEqual(hook.map_event(dict(base, notification_type="permission_prompt"))[1]["state"], "waiting")
        self.assertIsNone(hook.map_event(dict(base, notification_type="unrelated")))
        self.assertIsNone(hook.map_event({}))
