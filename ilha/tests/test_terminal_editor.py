import json
import os
import pty
import select
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
from xml.etree import ElementTree
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import terminal_activity
import ide_activity_bridge as ide
import app_events
import editor_extension


class TerminalEditorTests(unittest.TestCase):
    def test_title_does_not_include_command_arguments(self):
        self.assertEqual(terminal_activity.title_for(['sudo','pacman','-S','privado']),'Pacman em execução')
        self.assertEqual(terminal_activity.title_for(['/tmp/segredo','token']),'Comando no terminal')
        self.assertEqual(terminal_activity.title_for(['yay','privado']),'Yay em execução')

    def test_terminal_preserves_input_output_and_exit_without_recording_them(self):
        with tempfile.TemporaryDirectory() as temp:
            env=dict(os.environ,HOME=temp,XDG_CONFIG_HOME=temp,XDG_RUNTIME_DIR=temp)
            code='import sys;sys.stdout.write(sys.stdin.read());sys.stderr.write("saida-privada");raise SystemExit(7)'
            result=subprocess.run([sys.executable,str(SCRIPTS/'terminal_activity.py'),'--',sys.executable,'-c',code],
                env=env,input=b'entrada-privada',capture_output=True,timeout=5)
            self.assertEqual(result.returncode,7);self.assertEqual(result.stdout,b'entrada-privada')
            self.assertEqual(result.stderr,b'saida-privada')
            text=next((Path(temp)/'ilha/app-activities').glob('*.json')).read_text()
            self.assertNotIn('privada',text);self.assertNotIn(code,text)
            self.assertEqual(json.loads(text)['activity']['state'],'error')

    def test_bridge_generic_fields_unknown_exit_and_disconnect(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,XDG_RUNTIME_DIR=temp),patch.object(app_events,'config',return_value={}):
            bridge=ide.Bridge('vscodium')
            for key,kind,code,state in [('task','task',0,'success'),('fail','task',3,'error'),('debug','debug',0,'paused'),('missing','terminal',None,'paused')]:
                bridge.receive({'op':'start','id':key,'kind':kind,'command':'privado','path':'privado'})
                reporter=bridge.entries[key][0]
                bridge.receive({'op':'end','id':key,'exitCode':code})
                text=reporter.path.read_text();self.assertNotIn('privado',text)
                self.assertEqual(json.loads(text)['activity']['state'],state)
            bridge.receive({'op':'start','id':'close','kind':'task'});reporter=bridge.entries['close'][0]
            bridge.close();self.assertEqual(json.loads(reporter.path.read_text())['activity']['state'],'paused')
            with self.assertRaises(ValueError):bridge.receive({'op':'start','id':'$(bad)','kind':'task'})
            with self.assertRaises(ValueError):bridge.receive({'op':'execute','id':'ok','kind':'task'})

    def test_terminal_ctrl_c_preserves_terminal_signal_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            env=dict(os.environ,HOME=temp,XDG_CONFIG_HOME=temp,XDG_RUNTIME_DIR=temp)
            pid,master=pty.fork()
            if pid==0:
                os.execve(sys.executable,[sys.executable,str(SCRIPTS/'terminal_activity.py'),'--',sys.executable,
                    '-c','import time;print("READY",flush=True);time.sleep(20)'],env)
            output=b'';ended=False
            try:
                deadline=time.monotonic()+5
                while b'READY' not in output and time.monotonic()<deadline:
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,8192)
                self.assertIn(b'READY',output);os.write(master,b'\x03')
                while time.monotonic()<deadline:
                    done,status=os.waitpid(pid,os.WNOHANG)
                    if done:
                        ended=True;self.assertEqual(os.waitstatus_to_exitcode(status),130);break
                    time.sleep(.05)
                self.assertTrue(ended)
                text=next((Path(temp)/'ilha/app-activities').glob('*.json')).read_text()
                self.assertEqual(json.loads(text)['activity']['state'],'paused')
            finally:
                os.close(master)
                if not ended:
                    os.kill(pid,15);os.waitpid(pid,0)

    def test_bridge_never_spawns_payload_command(self):
        with tempfile.TemporaryDirectory() as temp:
            env=dict(os.environ,HOME=temp,XDG_CONFIG_HOME=temp,XDG_RUNTIME_DIR=temp)
            events=[{'op':'start','id':'safe','kind':'task','command':'TOKEN_PRIVADO'}, {'op':'end','id':'safe','exitCode':0}]
            result=subprocess.run([sys.executable,str(SCRIPTS/'ide_activity_bridge.py'),'--app','vscode'],env=env,
                input='\n'.join(json.dumps(event) for event in events)+'\n',capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0);self.assertEqual(result.stdout,'')
            text=next((Path(temp)/'ilha/app-activities').glob('*.json')).read_text()
            self.assertNotIn('TOKEN_PRIVADO',text);self.assertEqual(json.loads(text)['activity']['state'],'success')

    def test_vsix_contains_only_our_extension_and_valid_xml(self):
        with tempfile.TemporaryDirectory() as temp:
            output=editor_extension.build(Path(temp)/'test.vsix')
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(len(archive.namelist()),7)
                ElementTree.fromstring(archive.read('extension.vsixmanifest'))
                ElementTree.fromstring(archive.read('[Content_Types].xml'))
                self.assertEqual(json.loads(archive.read('extension/package.json'))['publisher'],'bielodragon')
                self.assertNotIn(b'node_modules',archive.read('extension/extension.js'))


if __name__=='__main__':unittest.main()
