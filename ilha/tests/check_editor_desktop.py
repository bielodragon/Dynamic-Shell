#!/usr/bin/env python3
"""Opt-in: instala VSIX em perfil temporário e executa tarefas/terminal reais do VSCodium."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from check_launcher_desktop import require_unlocked
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from editor_extension import build

ROOT=Path(__file__).resolve().parents[1]


def cleanup_test_editors():
    # Somente Electron com raiz exclusiva deste helper; nunca processos do perfil pessoal.
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            if path.stat().st_uid!=os.getuid():continue
            args=(path/'cmdline').read_bytes().split(b'\0')
            if not args or Path(os.fsdecode(args[0])).resolve()!=Path('/usr/share/vscodium/codium') or any(arg.startswith(b'--type=') for arg in args):continue
            roots=[arg.split(b'=',1)[1] for arg in args if arg.startswith(b'--user-data-dir=')]
            if b'--user-data-dir' in args:roots.append(args[args.index(b'--user-data-dir')+1])
            if any(root.startswith(b'/tmp/ilha-editor-test-') and root.endswith(b'/user') for root in roots):
                os.kill(int(path.name),signal.SIGTERM)
        except (OSError,IndexError):pass


def main():
    require_unlocked()
    cleanup_test_editors()
    with tempfile.TemporaryDirectory(prefix='ilha-editor-test-') as temp:
        folder=Path(temp);user=folder/'user';(user/'User').mkdir(parents=True)
        workspace=folder/'workspace';workspace.mkdir();extensions=folder/'extensions';extensions.mkdir()
        phase=folder/'phase';result=folder/'result.json';test=folder/'test.cjs'
        driver=folder/'driver';driver.mkdir()
        (driver/'package.json').write_text(json.dumps({'name':'ilha-test-driver','publisher':'local','version':'0.0.1',
            'engines':{'vscode':'^1.93.0'},'main':'./driver.cjs','contributes':{'debuggers':[{'type':'ilha-test','label':'Ilha test'}]}}))
        (driver/'driver.cjs').write_text('''const vscode=require('vscode');
exports.activate=context=>{context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('ilha-test',{
 createDebugAdapterDescriptor(){const emitter=new vscode.EventEmitter();let seq=1;
  return new vscode.DebugAdapterInlineImplementation({onDidSendMessage:emitter.event,dispose(){emitter.dispose();},handleMessage(message){
   if(message.type!=='request')return;
   emitter.fire({seq:seq++,type:'response',request_seq:message.seq,command:message.command,success:true,body:message.command==='initialize'?{supportsConfigurationDoneRequest:true}:{}});
   if(message.command==='launch')emitter.fire({seq:seq++,type:'event',event:'initialized'});
   if(message.command==='disconnect')emitter.fire({seq:seq++,type:'event',event:'terminated'});
  }});
 }
}));};''')
        settings={'telemetry.telemetryLevel':'off','update.mode':'none','extensions.autoUpdate':False,'extensions.ignoreRecommendations':True,
            'workbench.startupEditor':'none','terminal.integrated.shellIntegration.enabled':True,
            'ilhaActivities.bridgePath':str(ROOT/'scripts/ide_activity_bridge.py')}
        (user/'User/settings.json').write_text(json.dumps(settings))
        env=dict(os.environ,HOME=temp,XDG_CONFIG_HOME=str(folder/'config'),XDG_CACHE_HOME=str(folder/'cache'),
            XDG_DATA_HOME=str(folder/'data'))
        vsix=build(folder/'ilha.vsix')
        base=['/usr/bin/codium','--disable-gpu','--user-data-dir',str(user),'--extensions-dir',str(extensions)]
        installed=subprocess.run(base+['--install-extension',str(vsix)],env=env,capture_output=True,text=True,timeout=30)
        assert installed.returncode==0,installed.stdout+installed.stderr
        test.write_text('''const vscode=require('vscode');
const fs=require('node:fs');const path=require('node:path');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const directory=@@EVENTS@@,phase=@@PHASE@@,result=@@RESULT@@;
function events() {
 if(!fs.existsSync(directory))return [];
 return fs.readdirSync(directory).filter(name=>name.endsWith('.json')).flatMap(name=>{
  try {const item=JSON.parse(fs.readFileSync(path.join(directory,name),'utf8'));
   if(item.source!=='editors') return [];
   const status=fs.readFileSync('/proc/'+item.pid+'/status','utf8');
   return Number(status.match(/^PPid:\\s+(\\d+)/m)[1])===process.pid?[item.activity]:[];
  } catch {return [];}
 });
}
async function wait(predicate,timeout=15000) {
 const end=Date.now()+timeout;while(Date.now()<end){const value=predicate();if(value)return value;await delay(100);}
 throw Error('Estado esperado não chegou: '+JSON.stringify(events()));
}
exports.run=async()=>{
 const extension=vscode.extensions.getExtension('bielodragon.ilha-activities');
 if(!extension)throw Error('Extensão VSIX não encontrada');await extension.activate();
 const task=new vscode.Task({type:'ilha-test'},vscode.workspace.workspaceFolders[0],'Ilha teste','ilha',
  new vscode.ProcessExecution('/usr/bin/python3',['-c','import time;time.sleep(5)']));
 let terminal;
 try {
  await vscode.tasks.executeTask(task);
  const active=await wait(()=>events().find(row=>row.title.endsWith('Tarefa')&&row.state==='running'));
  fs.writeFileSync(phase,'task-running');
  await wait(()=>events().find(row=>row.id===active.id&&row.state==='success'));
  const failed=new vscode.Task({type:'ilha-test'},vscode.workspace.workspaceFolders[0],'Ilha erro','ilha',
   new vscode.ProcessExecution('/usr/bin/python3',['-c','raise SystemExit(7)']));
  await vscode.tasks.executeTask(failed);
  await wait(()=>events().find(row=>row.title.endsWith('Tarefa')&&row.state==='error'));
  terminal=vscode.window.createTerminal({name:'Ilha terminal de teste',shellPath:'/bin/bash'});
  await wait(()=>terminal.shellIntegration,20000);
  terminal.shellIntegration.executeCommand('/usr/bin/python3',['-c','import time;time.sleep(2)']);
  const command=await wait(()=>events().find(row=>row.title.endsWith('Terminal integrado')&&row.state==='running'));
  await wait(()=>events().find(row=>row.id===command.id&&row.state==='success'));
  await vscode.extensions.getExtension('local.ilha-test-driver').activate();
   if(!await vscode.debug.startDebugging(vscode.workspace.workspaceFolders[0],{type:'ilha-test',request:'launch',name:'Ilha depuração de teste'}))throw Error('Debugger de teste não iniciou');
   const debug=await wait(()=>events().find(row=>row.title.endsWith('Depuração')&&row.state==='running'));
   await vscode.debug.stopDebugging();
   await wait(()=>events().find(row=>row.id===debug.id&&row.state==='paused'));
  fs.writeFileSync(result,JSON.stringify({task:true,failure:true,terminal:true,debug:true}));
 } finally {if(terminal)terminal.dispose();}
};'''.replace('@@EVENTS@@',json.dumps(str(Path(os.environ['XDG_RUNTIME_DIR'])/'ilha/app-activities')))
            .replace('@@PHASE@@',json.dumps(str(phase))).replace('@@RESULT@@',json.dumps(str(result))))
        # O CLI pode desacoplar a GUI. O executável Electron mantém o processo sob controle do teste.
        args=['/usr/share/vscodium/codium',*base[1:],'--new-window','--skip-welcome','--skip-release-notes','--disable-workspace-trust',
            '--extensionDevelopmentPath',str(driver),'--extensionTestsPath',str(test),str(workspace)]
        with (folder/'editor.log').open('w+') as log:
            process=subprocess.Popen(args,env=env,stdout=log,stderr=log)
            captured=False
            try:
                deadline=time.monotonic()+60
                while process.poll() is None and time.monotonic()<deadline:
                    if not captured and phase.exists():
                        require_unlocked();time.sleep(.8)
                        subprocess.run(['grim','/tmp/ilha-editor-tarefa.png'],check=True,timeout=8);captured=True
                    time.sleep(.2)
                code=process.wait(timeout=5)
                log.seek(0);output=log.read()
                assert code==0 and result.exists(),output[-5000:]
                print('OK: VSIX instalado em perfil temporário; tarefa real, exit7 e terminal com shell integration. '+result.read_text())
                print('Captura: /tmp/ilha-editor-tarefa.png' if captured else 'Sem captura.')
            finally:
                if process.poll() is None:process.terminate();process.wait(timeout=5)
                cleanup_test_editors()


if __name__=='__main__':main()
