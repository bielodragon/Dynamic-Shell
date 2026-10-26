import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import desktop_setup as setup
import install_shell as installer
import theme_sync as sync


class DeliveryTests(unittest.TestCase):
    def test_user_and_system_install_are_staged_and_preserve_personal_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); personal = root / 'home/user/.config/ilha/config.json'
            personal.parent.mkdir(parents=True); personal.write_text('personal')
            with patch.dict(os.environ, {'HOME':'/home/user','XDG_CONFIG_HOME':'/home/user/.config'}):
                user = installer.install('user',root)
                system = installer.install('system',root)
                for result in (user,system):
                    self.assertTrue((Path(result['code']) / 'shell.qml').is_file())
                    wrapper = Path(result['commands']) / 'ilha'
                    self.assertTrue(wrapper.stat().st_mode & 0o111)
                    self.assertNotIn(str(root),wrapper.read_text())
                self.assertEqual(personal.read_text(),'personal')
                installer.install('user',root)
                self.assertTrue(list(Path(user['code']).parent.glob('ilha.bak.ilha-*')))

    def test_dry_run_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)/'empty'
            installer.install('system',destination,True)
            self.assertFalse(destination.exists())

    def test_managed_hyprland_block_is_idempotent_and_rolls_back_on_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); path=root/'hypr/hyprland.lua'; path.parent.mkdir(); path.write_text('-- original\n')
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}), patch.object(setup.subprocess,'run'), patch.object(setup.subprocess,'check_output',side_effect=lambda args,**kw: '[]' if '-j' in args else ''):
                setup.prepare_hyprland(True); first=path.read_text()
                setup.prepare_hyprland(True)
                self.assertEqual(path.read_text(),first)
                self.assertEqual(first.count('hl.on("hyprland.start"'),1)
                self.assertIn('hl.unbind("SUPER + SPACE")',first)
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}), patch.object(setup.subprocess,'run'), patch.object(setup.subprocess,'check_output',return_value='Erro de sintaxe'):
                with self.assertRaises(RuntimeError): setup.prepare_hyprland(True)
                self.assertEqual(path.read_text(),first)

    def test_bars_hide_restore_preserves_unrelated_preferences(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); path=root/'caelestia/shell.json'; path.parent.mkdir()
            original={'bar':{'tray':{'background':False}},'background':{'wallpaperEnabled':True}}
            path.write_text(json.dumps(original))
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}):
                setup.bars(hide=True)
                hidden=json.loads(path.read_text()); self.assertEqual(hidden['bar']['excludedScreens'],['^.*$'])
                self.assertEqual(hidden['background'],original['background'])
                setup.bars(restore=True)
                restored=json.loads(path.read_text())
                self.assertEqual(restored['bar'],original['bar'])
                self.assertNotIn('enabled',restored['sidebar'])

    def test_sync_is_opt_in_and_kitty_changes_are_backed_up(self):
        theme=json.loads((Path(__file__).resolve().parents[1]/'themes/dark.json').read_text())
        with patch.object(sync.subprocess,'run') as run:
            self.assertEqual(sync.synchronize({'theme':theme,'config':{}})['applied'],[])
            run.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); kitty=root/'kitty/kitty.conf'; kitty.parent.mkdir(); kitty.write_text('font_size 12\n')
            with patch.dict(os.environ,{'XDG_CONFIG_HOME':str(root)}):
                result=sync.synchronize({'theme':theme,'config':{'sync':{'kitty':True}}})
                self.assertEqual(result['applied'],['kitty'])
                self.assertIn('font_size 12',kitty.read_text())
                self.assertEqual(len(list(kitty.parent.glob('*.bak.ilha-*'))),1)
                sync.synchronize({'theme':theme,'config':{'sync':{'kitty':True}}})
                self.assertEqual(kitty.read_text().count('include '),1)

    def test_sync_portal_borders_and_partial_failure_are_reported(self):
        theme=json.loads((Path(__file__).resolve().parents[1]/'themes/dark.json').read_text())
        with patch.object(sync,'run') as run:
            result=sync.synchronize({'theme':theme,'config':{'sync':{'portal':True,'hyprland':True}}})
            self.assertEqual(result['applied'],['portal','hyprland'])
            self.assertEqual(run.call_args_list[0].args[0][-1],'prefer-dark')
            self.assertEqual(run.call_args_list[1].args[0][1:3],['keyword','general:col.active_border'])
        with patch.object(sync,'run',side_effect=RuntimeError('indisponível')):
            result=sync.synchronize({'theme':theme,'config':{'sync':{'portal':True}}})
            self.assertFalse(result['ok']); self.assertIn('portal:',result['errors'][0])


if __name__ == '__main__': unittest.main()
