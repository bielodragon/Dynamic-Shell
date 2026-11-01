#!/usr/bin/env python3
"""Painel QML real com backend sintético; nenhuma rede/dispositivo pessoal é alterado."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-connectivity-test-') as temp:
        folder=Path(temp)
        for name in ('services','components','modules'):(folder/name).symlink_to(ROOT/name,target_is_directory=True)
        scripts=folder/'scripts';scripts.mkdir()
        for path in (ROOT/'scripts').glob('*.py'):
            if path.name not in ('connectivity_service.py','system_controls.py'):(scripts/path.name).symlink_to(path)
        (scripts/'system_controls.py').write_text('import json\nprint(json.dumps({"ok":True,"state":{}}))\n')
        (scripts/'connectivity_service.py').write_text('''import json,sys
mode='wifi'
def state():
 data={'available':True,'enabled':True,'hardware':True}
 if mode=='wifi':data['networks']=[{'id':'ap1','ssid':'Ilha teste','interface':'wlan-test','security':'wpa-psk','saved':False,'connected':False,'strength':87}]
 else:data['devices']=[{'id':'blue1','name':'Fone de teste','paired':False,'connected':False,'trusted':False,'blocked':False,'battery':80}]
 print(json.dumps({'type':'state','mode':mode,'state':data,'busy':False,'message':''}),flush=True)
state()
for line in sys.stdin:
 value=json.loads(line)
 if value['action']=='mode':mode=value['mode'];state()
 elif value['action']=='wifi-connect':
  assert value['password']=='senha-de-teste-123'
  print(json.dumps({'type':'error','message':'Senha recebida por stdin, sem argv.'}),flush=True)
 elif value['action']=='blue-pair':
  print(json.dumps({'type':'challenge','id':1,'kind':'confirm','code':'123456','device':'Fone de teste'}),flush=True)
 elif value['action']=='answer':
  assert value['id']==1 and value['accept'] is True
  print(json.dumps({'type':'challenge','kind':''}),flush=True)
  print(json.dumps({'type':'error','message':'Pareamento confirmado pelo usuário.'}),flush=True)
''')
        runtime=folder/'runtime';runtime.mkdir(mode=0o700)
        env=dict(os.environ,HOME=temp,XDG_CONFIG_HOME=str(folder/'config'),XDG_RUNTIME_DIR=str(runtime),QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='generic')
        (folder/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.components
ShellRoot {
 FloatingWindow { width:520;height:650;ConnectivityPanel { id:panel;anchors.fill:parent } }
 function find(item,name) { if(item.objectName===name)return item;for(const child of item.children || []){const result=find(child,name);if(result)return result;}return null; }
 IpcHandler {
  target:"test"
  function wifi():void { ControlCenterState.opened=true;ConnectivityState.open("wifi"); }
  function blue():void { ConnectivityState.open("bluetooth"); }
  function connect():void { panel.selected=ConnectivityState.state.networks[0];find(panel,"wifiPassword").text="senha-de-teste-123";find(panel,"connectionAction").clicked(); }
  function pair():void { panel.selected=ConnectivityState.state.devices[0];find(panel,"connectionAction").clicked(); }
  function confirm():void { ConnectivityState.action("answer",{id:ConnectivityState.challenge.id,accept:true}); }
  function close():void { ControlCenterState.close(); }
  function check():string { const component=Qt.createComponent("modules/ControlCenter.qml");return JSON.stringify({error:component.errorString(),status:component.status,cleared:find(panel,"wifiPassword").text==="",challenge:ConnectivityState.challenge.kind || ""}); }
 }
}''')
        with (folder/'qml.log').open('w+') as log:
            process=subprocess.Popen(['/usr/bin/quickshell','-p',temp,'--no-color'],env=env,stdout=log,stderr=log)
            def ipc(method,target='test'):
                return subprocess.run(['/usr/bin/quickshell','ipc','--pid',str(process.pid),'call',target,method],env=env,capture_output=True,text=True,timeout=3)
            def wait(predicate):
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    try:
                        value=json.loads(ipc('status','connectivity').stdout)
                        if predicate(value):return value
                    except (ValueError,KeyError):pass
                    time.sleep(.1)
                log.seek(0);raise AssertionError(log.read())
            try:
                wait(lambda value:value['mode']=='')
                result=json.loads(ipc('check').stdout)
                assert result['status']==1 or result['error'].endswith('No PanelWindow backend loaded.\n'),result
                ipc('wifi');wait(lambda value:value['ready'] and len(value['state'].get('networks',[]))==1)
                ipc('connect');wait(lambda value:'stdin' in value['message'])
                assert json.loads(ipc('check').stdout)['cleared']
                ipc('blue');wait(lambda value:len(value['state'].get('devices',[]))==1)
                ipc('pair')
                deadline=time.monotonic()+4
                while not json.loads(ipc('check').stdout)['challenge'] and time.monotonic()<deadline:time.sleep(.1)
                assert json.loads(ipc('check').stdout)['challenge']=='confirm'
                ipc('confirm');wait(lambda value:'confirmado' in value['message'])
                ipc('close');wait(lambda value:value['mode']=='' and not value['busy'])
                log.seek(0);output=log.read()
                assert not any(word in output for word in ('ERROR','TypeError','ReferenceError','Cannot assign','Unable to assign','Binding loop')),output
                assert 'senha-de-teste-123' not in output
                print('OK: painel QML real offscreen, senha por stdin e campo limpo, pareamento confirmado e fechamento sem redes reais. Layer-shell exige teste nativo.')
            finally:
                process.terminate();process.wait(timeout=5)


if __name__=='__main__':main()
