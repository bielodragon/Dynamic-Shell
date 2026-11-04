import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import session_actions as session
import system_controls as controls


class SessionTests(unittest.TestCase):
    def which(self,name):return '/usr/bin/'+name if name in ('caelestia','omarchy-shell','hyprctl','uwsm') else None
    def probe(self,args):
        if args[0].endswith('caelestia'):return 'false'
        if args[0].endswith('omarchy-shell'):return None
        if args[-1]=='version':return json.dumps({'version':'0.56.2'})
        if args[-1]=='instances':return json.dumps([{'instance':'teste','pid':123}])
        if args[1]=='eval':return 'ok'
        return None
    def test_caelestia_active_wins_over_omarchy_merely_installed(self):
        with patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',side_effect=self.probe):
            plan=session.lock_plan();self.assertEqual(plan['provider'],'Caelestia')
            self.assertEqual(plan['command'],['/usr/bin/caelestia','shell','lock','lock'])
    def test_no_inactive_shell_is_launched_and_standalone_failure_is_reported(self):
        with patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',return_value=None):self.assertIsNone(session.lock_plan())
        child=Mock();child.wait.return_value=1
        with patch.object(session.subprocess,'Popen',return_value=child):
            with self.assertRaisesRegex(RuntimeError,'erro'):session.execute({'command':['hyprlock'],'detached':True},locking=True)
    def test_existing_lock_is_kept_without_starting_another(self):
        def probe(args):return 'true' if args[0].endswith('omarchy-shell') else 'false'
        with patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',side_effect=probe),patch.object(session.subprocess,'run') as execute:
            plan=session.lock_plan();self.assertEqual(plan['provider'],'Omarchy');session.execute(plan,locking=True);execute.assert_not_called()
    def test_plain_hyprland_session_does_not_use_uwsm_binary(self):
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='teste'),patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',side_effect=self.probe),patch.object(session.Path,'read_text',return_value='0::/user.slice/session-7.scope\n'):
            plan=session.logout_plan();self.assertEqual(plan['provider'],'Hyprland')
            self.assertEqual(plan['command'],['/usr/bin/hyprctl','dispatch','hl.dsp.exit()'])
    def test_only_actual_compositor_uwsm_unit_uses_uwsm_stop(self):
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='teste'),patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',side_effect=self.probe),patch.object(session.Path,'read_text',return_value='0::/user.slice/wayland-wm@hyprland.desktop.service\n'):
            self.assertEqual(session.logout_plan()['command'],['/usr/bin/uwsm','stop'])
        self.assertFalse(session.uwsm_cgroup('0::/user.slice/graphical-session.target'))
    def test_legacy_hyprland_uses_legacy_dispatch(self):
        def probe(args):return '{"version":"0.49.0"}' if args[-1]=='version' else '[]'
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='teste'),patch.object(session.shutil,'which',side_effect=self.which),patch.object(session,'probe',side_effect=probe):
            self.assertEqual(session.logout_plan()['command'][-1],'exit')
    def test_failed_ipc_is_not_success_even_with_exit_code_zero(self):
        with patch.object(session.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'Function not found.','')):
            with self.assertRaises(RuntimeError):session.execute({'command':['caelestia','shell','lock','lock'],'detached':False},locking=True)
    def test_lock_and_logout_dispatch_only_after_explicit_confirmation(self):
        with patch.object(controls,'capabilities',return_value={'lock':True,'logout':True}),patch.object(session,'lock') as lock,patch.object(session,'logout') as logout:
            for name in ('lock','logout'):
                with self.assertRaises(ValueError):controls.action(name)
            lock.assert_not_called();logout.assert_not_called()
            controls.action('lock',confirmed=True);lock.assert_called_once()
            controls.action('logout',confirmed=True);logout.assert_called_once()
    def test_logind_failure_does_not_disable_working_lock_and_logout(self):
        import dbus
        with patch.object(session,'lock_plan',return_value={'provider':'Caelestia'}),patch.object(session,'logout_plan',return_value={'provider':'Hyprland'}),patch.object(dbus,'SystemBus',side_effect=dbus.DBusException('indisponível')):
            state=controls.capabilities();self.assertTrue(state['lock']);self.assertTrue(state['logout']);self.assertFalse(state['poweroff'])


if __name__=='__main__':unittest.main()
