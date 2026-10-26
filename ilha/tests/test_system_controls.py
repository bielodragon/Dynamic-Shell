import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import system_controls as controls


class ControlTests(unittest.TestCase):
    def test_rejects_invalid_values_before_running_any_command(self):
        with patch.object(controls, 'run') as execute:
            for value in (True, '50', -1, 101, float('nan')):
                with self.assertRaises(ValueError): controls.action('volume', value)
            with self.assertRaises(ValueError): controls.action('brightness', 0)
            with self.assertRaises(ValueError): controls.action('wifi', 'off; false')
            with self.assertRaises(ValueError): controls.action('arbitrary-command', 'hello')
            execute.assert_not_called()

    def test_volume_has_limit_and_wifi_uses_literal_arguments(self):
        with patch.object(controls, 'run') as execute:
            controls.action('volume', 42)
            execute.assert_called_with(['wpctl', 'set-volume', '--limit', '1.0', '@DEFAULT_AUDIO_SINK@', '42%'])
            controls.action('wifi', False)
            execute.assert_called_with(['nmcli', 'radio', 'wifi', 'off'])

    def test_power_requires_explicit_confirmation_and_capability(self):
        with patch.object(controls, 'run') as execute, patch.object(controls, 'capabilities', return_value={}):
            for action in ('poweroff', 'reboot', 'suspend', 'lock', 'logout'):
                with self.assertRaises(ValueError): controls.action(action)
                with self.assertRaises(RuntimeError): controls.action(action, confirmed=True)
            execute.assert_not_called()

    def test_profile_must_be_reported_by_system(self):
        with patch.object(controls, 'profiles', return_value={'profiles': ['balanced']}), patch.object(controls, 'run') as execute:
            with self.assertRaises(ValueError): controls.action('profile', 'performance')
            execute.assert_not_called()
            controls.action('profile', 'balanced')
            execute.assert_called_with(['powerprofilesctl', 'set', 'balanced'])

    def test_airplane_restores_previous_states_and_keeps_original_on_reapply(self):
        import dbus
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(controls, 'network', return_value={'wifi': False, 'wwan': True}), \
                patch.object(controls, 'bluetooth', return_value={'available': True, 'adapters': [{'path': '/org/bluez/hci0', 'powered': False}]}), \
                patch.object(controls, 'run') as execute, patch.object(controls, 'set_bluetooth') as blue, \
                patch.object(dbus, 'SystemBus'), patch.object(dbus, 'Interface') as interface:
            controls.airplane(True)
            file = Path(directory) / 'ilha/radios.json'
            original = file.read_text()
            controls.airplane(True)
            self.assertEqual(original, file.read_text())
            blue.assert_called_with(False)
            controls.airplane(False)
            self.assertFalse(file.exists())
            self.assertIn(unittest.mock.call(['nmcli', 'radio', 'wifi', 'off']), execute.call_args_list)
            self.assertIn(unittest.mock.call(['nmcli', 'radio', 'wwan', 'on']), execute.call_args_list)
            self.assertFalse(bool(interface.return_value.Set.call_args.args[2]))

    def test_snapshot_failure_is_local_to_one_control(self):
        functions = ('network', 'bluetooth', 'audio', 'brightness', 'profiles', 'battery', 'capabilities')
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in functions: stack.enter_context(patch.object(controls, name, return_value={'available': True}))
            stack.enter_context(patch.object(controls, 'brightness', side_effect=RuntimeError('Sem hardware')))
            value = controls.snapshot()
            self.assertTrue(value['network']['available'])
            self.assertFalse(value['brightness']['available'])
            self.assertEqual(value['brightness']['error'], 'Sem hardware')


if __name__ == '__main__': unittest.main()
