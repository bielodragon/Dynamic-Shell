#!/usr/bin/env python3
"""Bateria e preferências QML com sensores/efeitos simulados e dados privados."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-device-test-') as folder:
        root=Path(folder)
        for name in ('services','components'): (root/name).symlink_to(ROOT/name,target_is_directory=True)
        scripts=root/'scripts';scripts.mkdir()
        (scripts/'theme_store.py').symlink_to(ROOT/'scripts/theme_store.py')
        sensor=root/'sensor.json';sensor.write_text(json.dumps({'battery':{'available':False,'batteries':[]}}))
        (scripts/'device_metrics.py').write_text('import json,time,sys\nfrom pathlib import Path\nwhile True:\n d=json.loads(Path('+repr(str(sensor))+').read_text())\n if "--metrics" in sys.argv:d["cpu"]=25;d["memory"]={"percent":40}\n print(json.dumps(d),flush=True)\n time.sleep(.1)\n')
        (scripts/'monitor_controls.py').write_text('import json\nprint(json.dumps({"ok":True,"state":{"performance":False,"mangoAvailable":True,"games":0}}))\n')
        (root/'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
import qs.components
ShellRoot {
    FloatingWindow { visible: true; implicitWidth: 200; implicitHeight: 50; DeviceBattery { id: battery } }
    IpcHandler {
        target: "device-test"
        function status(): string { return JSON.stringify({ready:ThemeStore.ready,batteryVisible:battery.visible,batteryText:battery.text}); }
    }
}''')
        env=dict(os.environ,XDG_CONFIG_HOME=str(root/'config'),QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='generic')
        with (root/'log').open('w+') as log:
            process=subprocess.Popen(['/usr/bin/quickshell','-p',str(root),'--no-color'],env=env,stdout=log,stderr=log)
            def ipc(target,method,*args):
                return subprocess.check_output(['/usr/bin/quickshell','ipc','--pid',str(process.pid),'call',target,method,*args],text=True,stderr=subprocess.DEVNULL,timeout=3)
            def wait(predicate):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    try:
                        data=json.loads(ipc('device','status'));ui=json.loads(ipc('device-test','status'))
                        if ui['ready'] and not data['busy'] and predicate(data,ui):return
                    except (ValueError,subprocess.SubprocessError):pass
                    time.sleep(.1)
                log.seek(0);raise AssertionError(str(data)+'\n'+str(ui)+'\n'+log.read())
            try:
                wait(lambda d,u:not u['batteryVisible'] and 'battery' in d['data'])
                sensor.write_text(json.dumps({'battery':{'available':True,'batteries':[{'percent':42,'status':'Charging'}]}}))
                wait(lambda d,u:u['batteryVisible'] and '42%' in u['batteryText'])
                ipc('device','setMetrics','true');wait(lambda d,u:d['data'].get('cpu')==25)
                ipc('device','setMetrics','false');wait(lambda d,u:'cpu' not in d['data'])
                ipc('device','setFps','true');wait(lambda d,u:d['fps'])
                saved=json.loads((root/'config/ilha/config.json').read_text())
                assert saved['monitoring']['fps'] and not saved['monitoring']['metrics']
                sensor.write_text(json.dumps({'battery':{'available':False,'batteries':[]}}))
                wait(lambda d,u:not u['batteryVisible'])
                log.seek(0);text=log.read()
                assert not any(marker in text for marker in ('ERROR','TypeError','ReferenceError')),text
                print('OK: bateria ausente/presente/carga, widget, métricas ligam/desligam observação e preferências FPS persistem.')
            finally:process.terminate();process.wait(timeout=5)


if __name__=='__main__':main()
