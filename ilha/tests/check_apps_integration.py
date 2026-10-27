#!/usr/bin/env python3
"""QML e wrappers reais com processos/arquivos sintéticos, sem jogos ou rede."""
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-apps-test-') as temp:
        folder=Path(temp)
        for name in ('services','components','scripts'):(folder/name).symlink_to(ROOT/name,target_is_directory=True)
        runtime=folder/'runtime';runtime.mkdir(mode=0o700)
        binary=folder/'bin';binary.mkdir()
        fake=binary/'localsend-cli'
        fake.write_text('#!'+sys.executable+'\nimport sys\nprint("READY",flush=True)\nassert sys.stdin.readline().strip()=="escolha-manual"\nprint("S privado [##--] 1.0 MB / 4.0 MB [1 MB/s] [ETA: 3s]",flush=True)\nprint("S privado: Sent 1 file (4 MB, took 2s)",flush=True)\n')
        fake.chmod(0o700)
        env=dict(os.environ,HOME=temp,XDG_RUNTIME_DIR=str(runtime),XDG_CONFIG_HOME=str(folder/'config'),XDG_DATA_HOME=str(folder/'data'),
            XDG_CACHE_HOME=str(folder/'cache'),PATH=str(binary)+':'+os.environ['PATH'],QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='generic')
        # Saída e código do Java continuam chegando ao launcher; segredo nunca vira atividade.
        java=folder/'java.py';java.write_text('print("Reloading ResourceManager: vanilla")\nprint("CHAT segredo-do-teste")\nraise SystemExit(7)\n')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/minecraft_activity.py'),'--',sys.executable,str(java)],env=env,capture_output=True,timeout=8)
        assert result.returncode==7 and b'CHAT segredo-do-teste' in result.stdout,result
        files=list((runtime/'ilha/app-activities').glob('*.json'));assert len(files)==1
        event=json.loads(files[0].read_text());assert event['activity']['state']=='error'
        assert 'segredo-do-teste' not in files[0].read_text()
        # PTY interativo real: o wrapper deve aguardar entrada, sem escolher destinatário.
        master,slave=pty.openpty()
        process=subprocess.Popen([sys.executable,str(ROOT/'scripts/localsend_activity.py')],env=env,stdin=slave,stdout=slave,stderr=slave)
        os.close(slave);output=b''
        try:
            deadline=time.monotonic()+6
            while b'READY' not in output and time.monotonic()<deadline:
                if select.select([master],[],[],.2)[0]:output+=os.read(master,8192)
            assert b'READY' in output,output
            assert process.poll() is None,'Não deve aceitar nem escolher por conta própria.'
            os.write(master,b'escolha-manual\n')
            while process.poll() is None and time.monotonic()<deadline:
                if select.select([master],[],[],.2)[0]:
                    try:output+=os.read(master,8192)
                    except OSError:break
            assert process.wait(timeout=3)==0,output
        finally:
            os.close(master)
            if process.poll() is None:process.terminate();process.wait(timeout=3)
        events=[json.loads(p.read_text()) for p in (runtime/'ilha/app-activities').glob('*.json')]
        assert any(e['source']=='localsend' and e['activity']['state']=='success' for e in events),events
        assert 'privado' not in json.dumps(events)
        # Nova atividade duradoura para observar atualização, remoção e preferências no QML.
        path=runtime/'ilha/app-activities/qml-fixture.json'
        payload={'source':'minecraft','pid':os.getpid(),'expires':time.time()+30,'activity':{'id':'minecraft:test','app':'Minecraft Java','title':'Prévia','detail':'Cliente inicializado','state':'running','progress':None,'ttl':12}}
        path.write_text(json.dumps(payload))
        (folder/'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
ShellRoot {
 readonly property bool loaded: AppIntegrationsState.enabled
 IpcHandler { target:"test"; function disable():void { ThemeStore.setPreferences({integrations:{steam:false,localsend:false,minecraft:false,terminal:false,editors:false}}); } }
}''')
        with (folder/'qml.log').open('w+') as log:
            process=subprocess.Popen(['/usr/bin/quickshell','-p',temp,'--no-color'],env=env,stdout=log,stderr=log)
            def call(target,method):
                result=subprocess.run(['/usr/bin/quickshell','ipc','--pid',str(process.pid),'call',target,method],env=env,capture_output=True,text=True,timeout=3)
                return json.loads(result.stdout) if result.stdout.strip() else None
            def wait(check):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    try:
                        if check():return
                    except (ValueError,TypeError,KeyError):pass
                    time.sleep(.15)
                log.seek(0);raise AssertionError(log.read())
            try:
                wait(lambda:'minecraft:test' in call('app-integrations','status')['activities'])
                wait(lambda:any(row['id']=='minecraft:test' for row in call('activities','list')['activities']))
                path.unlink()
                wait(lambda:'minecraft:test' not in call('app-integrations','status')['activities'])
                call('test','disable');wait(lambda:not call('app-integrations','status')['enabled'])
                assert not call('activities','list')['activities']
                log.seek(0);output=log.read();assert not any(word in output for word in ('ERROR','TypeError','ReferenceError')),output
            finally:process.terminate();process.wait(timeout=5)
        print('OK: wrapper Java, código de saída, privacidade dos eventos, LocalSend PTY com escolha manual, observador QML, remoção e fontes desativadas. Nenhum jogo ou transferência real iniciado.')


if __name__=='__main__':main()
