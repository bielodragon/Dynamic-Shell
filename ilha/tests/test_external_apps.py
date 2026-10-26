import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import external_apps


class ExternalAppsTests(unittest.TestCase):
    def test_missing_hyprmod_is_reported_without_trying_install(self):
        with patch.object(external_apps.shutil, 'which', return_value=None), patch.object(external_apps.subprocess, 'Popen') as launch:
            self.assertFalse(external_apps.perform('check')['available'])
            with self.assertRaisesRegex(ValueError, 'não está instalado'): external_apps.perform('launch')
            launch.assert_not_called()

    def test_unknown_operation_is_not_executed(self):
        with self.assertRaises(ValueError): external_apps.perform('arbitrary')
