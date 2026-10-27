import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import install_dependencies as deps
import build_release
import install_shell


class DependencyTests(unittest.TestCase):
    def plan(self,**kwargs):
        return deps.plan(['core',*kwargs.pop('modules',[])],**kwargs)

    def test_satisfied_providers_are_not_replaced(self):
        with patch.object(deps.shutil,'which',return_value='/bin/tool'),patch.object(deps,'satisfied',return_value='provedor existente'),patch.object(deps,'repository') as repo:
            result=self.plan(modules=['wallpaper','fps32']);self.assertEqual(result['repositories'],[]);repo.assert_not_called()

    def test_aur_disabled_blocks_all_mutations_before_repository_install(self):
        with patch.object(deps.shutil,'which',return_value='/bin/tool'),patch.object(deps,'satisfied',return_value=''),patch.object(deps,'repository',return_value=None):
            result=self.plan(modules=['localsend']);self.assertIn('localsend-bin',result['aur'])
        with patch.object(deps.os,'geteuid',return_value=1000),patch.object(deps.subprocess,'run') as execute:
            with self.assertRaisesRegex(ValueError,'pendências'):deps.apply(result)
            execute.assert_not_called()

    def test_aur_allowed_adds_build_tools_but_never_installs_helper(self):
        def found(name,minimum=''):
            return None if name=='localsend' else {'repository':'extra','package':name,'version':'1'}
        with patch.object(deps.shutil,'which',side_effect=lambda name:'/bin/'+name if name in ('pacman','yay') else None),patch.object(deps,'satisfied',return_value=''),patch.object(deps,'repository',side_effect=found):
            result=self.plan(modules=['localsend'],allow_aur=True)
            self.assertFalse(result['blocked']);self.assertEqual(result['helper'],'yay')
            self.assertTrue({'base-devel','git'}<=set(row['package'] for row in result['repositories']))
            commands=deps.commands_for(result);self.assertIn('--aur',commands[-1]);self.assertNotIn('sudo',commands[-1]);self.assertNotIn('--noconfirm',commands[-1])

    def test_root_and_noninteractive_apply_are_rejected(self):
        result={'blocked':[],'repositories':[{'package':'python'}],'aur':[],'manager':'pacman','helper':None}
        with patch.object(deps.os,'geteuid',return_value=0),patch.object(deps.subprocess,'run') as execute:
            with self.assertRaisesRegex(ValueError,'sem sudo'):deps.apply(result)
            execute.assert_not_called()
        with patch.object(deps.os,'geteuid',return_value=1000),patch.object(deps.sys.stdin,'isatty',return_value=False):
            with self.assertRaisesRegex(ValueError,'terminal'):deps.apply(result)

    def test_cancel_is_readonly_and_confirm_uses_argument_arrays(self):
        result={'blocked':[],'repositories':[{'package':'python'}],'aur':[],'manager':'pacman','helper':None}
        with patch.object(deps.os,'geteuid',return_value=1000),patch.object(deps.sys.stdin,'isatty',return_value=True),patch.object(deps,'run_read',return_value=subprocess.CompletedProcess([],0,'extra/python 3 (1 bytes)','')),patch.object(deps.subprocess,'run') as execute,contextlib.redirect_stdout(io.StringIO()):
            with patch('builtins.input',return_value='n'):deps.apply(result)
            execute.assert_not_called()
            with patch('builtins.input',return_value='sim'):deps.apply(result)
            self.assertEqual(execute.call_args.args[0],['sudo','pacman','-S','--needed','--','python'])

    def test_repository_priority_and_quickshell_minimum(self):
        text='Repository : omarchy\nName : quickshell\nVersion : 0.3.2\n\nRepository : extra\nName : quickshell\nVersion : 0.3.1\n'
        with patch.object(deps,'run_read',side_effect=[subprocess.CompletedProcess([],0,text,''),subprocess.CompletedProcess([],0,'1\n','')]):
            self.assertEqual(deps.repository('quickshell','0.3.1')['repository'],'omarchy')
        with patch.object(deps,'run_read',side_effect=[subprocess.CompletedProcess([],0,text,''),subprocess.CompletedProcess([],0,'-1\n','')]):
            self.assertIsNone(deps.repository('quickshell','0.4.0'))

    def test_staged_user_and_system_include_all_current_commands(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HOME='/home/test',XDG_CONFIG_HOME='/home/test/.config'):
            for mode in ('user','system'):
                result=install_shell.install(mode,Path(temp))
                for command in ('ilha-deps','ilha-editor','ilha-run','ilha-minecraft','ilha-localsend','ilha-game','ilha-apps','ilha-activity','ilha'):
                    self.assertTrue((Path(result['commands'])/command).stat().st_mode&0o111)
                self.assertTrue((Path(result['code'])/'integrations/vscode/package.json').exists())

    def test_release_reproducible_excludes_checkpoint_and_rejects_dirty_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo';root.mkdir()
            def git(*args):subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
            git('init');git('config','user.name','Teste');git('config','user.email','teste@example.invalid')
            (root/'shell.qml').write_text('teste');(root/'RETOMADA.md').write_text('privado')
            (root/'.gitattributes').write_text('RETOMADA.md export-ignore\n')
            git('add','.');git('commit','-m','fixture')
            output=Path(temp)/'dist';archive,checksum,_=build_release.build(root,output);first=archive.read_bytes()
            self.assertTrue(checksum.read_text().startswith(hashlib.sha256(first).hexdigest()))
            build_release.build(root,output);self.assertEqual(first,archive.read_bytes())
            with tarfile.open(archive) as source:self.assertNotIn('ilha-shell/RETOMADA.md',source.getnames())
            (root/'shell.qml').write_text('modificado')
            with self.assertRaisesRegex(ValueError,'commite'):build_release.build(root,output)


if __name__=='__main__':unittest.main()
