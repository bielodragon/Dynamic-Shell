"""Exercita persistência sem tocar na configuração real do usuário."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "theme_store.py"


class ThemeStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = dict(os.environ, XDG_CONFIG_HOME=self.temp.name)

    def call(self, operation, payload=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), operation, json.dumps(payload or {})],
            env=self.env, text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def test_presets_and_oled(self):
        response = self.call("snapshot")
        self.assertTrue(response["ok"])
        self.assertEqual(len(response["themes"]), 10)
        oled = next(theme for theme in response["themes"] if theme["id"] == "oled")
        self.assertEqual(oled["colors"]["background"], "#000000")
        self.assertEqual(oled["glassOpacity"], 1)

    def test_custom_lifecycle_and_builtin_protection(self):
        original = next(theme for theme in self.call("snapshot")["themes"] if theme["id"] == "dark")
        edited = dict(original, name="Meu tema", colors=dict(original["colors"], accent="#123456"))
        saved = self.call("save", {"theme": edited})
        self.assertTrue(saved["ok"])
        custom_id = saved["config"]["theme"]
        self.assertTrue((Path(self.temp.name) / "ilha" / "themes" / f"{custom_id}.json").is_file())
        self.assertFalse(self.call("save", {"id": "dark", "theme": edited})["ok"])
        duplicate = self.call("duplicate", {"id": custom_id})
        self.assertTrue(duplicate["ok"])
        self.assertNotEqual(duplicate["config"]["theme"], custom_id)
        self.assertFalse(self.call("delete", {"id": "dark"})["ok"])
        self.assertTrue(self.call("delete", {"id": duplicate["config"]["theme"]})["ok"])
        self.assertEqual(self.call("snapshot")["config"]["theme"], "dark")

    def test_export_import_and_overrides(self):
        destination = Path(self.temp.name) / "tema.json"
        self.assertTrue(self.call("export", {"id": "nord", "path": str(destination)})["ok"])
        self.assertFalse(self.call("export", {"id": "nord", "path": str(destination)})["ok"])
        imported = self.call("import", {"path": str(destination)})
        self.assertTrue(imported["ok"])
        self.assertEqual(next(theme for theme in imported["themes"] if theme["id"] == imported["config"]["theme"])["name"], "Nord")
        self.assertFalse(self.call("overrides", {"values": {"accent": "blue"}})["ok"])
        updated = self.call("overrides", {"values": {"accent": "#abcdef", "glassOpacity": 0.75}})
        self.assertEqual(updated["config"]["overrides"]["glassOpacity"], 0.75)
        self.assertEqual(self.call("snapshot")["config"]["overrides"]["accent"], "#abcdef")

    def test_workspace_style_is_persisted_and_validated(self):
        self.assertEqual(self.call("snapshot")["config"]["workspaceStyle"], "icons")
        changed = self.call("workspace_style", {"style": "dots"})
        self.assertTrue(changed["ok"])
        self.assertEqual(self.call("snapshot")["config"]["workspaceStyle"], "dots")
        self.assertFalse(self.call("workspace_style", {"style": "other"})["ok"])
        self.assertEqual(self.call("snapshot")["config"]["workspaceStyle"], "dots")

    def test_do_not_disturb_is_persisted_and_validated(self):
        self.assertFalse(self.call("snapshot")["config"]["doNotDisturb"])
        self.assertTrue(self.call("do_not_disturb", {"enabled": True})["ok"])
        self.assertTrue(self.call("snapshot")["config"]["doNotDisturb"])
        self.assertFalse(self.call("do_not_disturb", {"enabled": "yes"})["ok"])
        self.assertTrue(self.call("snapshot")["config"]["doNotDisturb"])

    def test_preferences_merge_preserves_theme_and_rejects_partial_invalid_update(self):
        self.call('select', {'id': 'nord'})
        self.call('overrides', {'values': {'accent': '#abcdef'}})
        response = self.call('preferences', {'values': {'modules': {'media': False}, 'animations': {'enabled': False}}})
        self.assertTrue(response['ok'])
        self.assertFalse(response['config']['modules']['media'])
        self.assertTrue(response['config']['modules']['privacy'])
        self.assertEqual(response['config']['theme'], 'nord')
        self.assertEqual(response['config']['overrides']['accent'], '#abcdef')
        original = self.call('snapshot')['config']
        invalid = self.call('preferences', {'values': {'modules': {'media': True}, 'animations': {'scale': 0}}})
        self.assertFalse(invalid['ok'])
        self.assertEqual(original, self.call('snapshot')['config'])

    def test_preferences_validate_types_and_ranges(self):
        for values in ({'modules': {'privacy': 'false'}}, {'modules': {'madeUp': True}},
                       {'animations': {'scale': True}}, {'animations': {'scale': float('nan')}},
                       {'island': {'topMargin': -1}}, {'maxVisibleWorkspaces': 13}, {'unknown': 1}):
            self.assertFalse(self.call('preferences', {'values': values})['ok'])
        self.assertTrue(self.call('preferences', {'values': {'animations': {'scale': 2},
            'island': {'hoverExpandDelayMs': 0}, 'maxVisibleWorkspaces': 12}})['ok'])


if __name__ == "__main__":
    unittest.main()
