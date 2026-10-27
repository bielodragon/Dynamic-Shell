#!/usr/bin/env python3
"""Opt-in: lê sensores, reduz/restaura efeitos e valida MangoHud com glxgears."""
import json
import os
import subprocess
import time
from check_launcher_desktop import require_unlocked

BASE=['/usr/bin/quickshell','-c','ilha','ipc','call']
KEYS=['decoration:blur:enabled','animations:enabled','decoration:shadow:enabled']


def ipc(target,method,*args):return subprocess.check_output(BASE+[target,method,*args],text=True,timeout=5)
def status():return json.loads(ipc('device','status'))
def effects():return {key:json.loads(subprocess.check_output(['hyprctl','-j','getoption',key],text=True))['bool'] for key in KEYS}
def wait(predicate):
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        state=status()
        if not state['busy'] and predicate(state):return state
        time.sleep(.15)
    raise RuntimeError('Estado esperado não chegou: '+str(status()))


def main():
    require_unlocked()
    previous=status();before=effects();process=None
    try:
        ipc('device','setMetrics','true');wait(lambda s:s['data'].get('cpu') is not None)
        ipc('device','setPerformance','true');wait(lambda s:s['controls'].get('performance'))
        assert not any(effects().values())
        ipc('device','setPerformance','false');wait(lambda s:not s['controls'].get('performance'))
        assert effects()==before
        with open('/tmp/ilha-mangohud-test.log','w') as log:
            process=subprocess.Popen(['python3','ilha/scripts/game_runner.py','--opengl','--','glxgears'],stdout=log,stderr=log,start_new_session=True)
            time.sleep(3)
            assert process.poll() is None,'Janela OpenGL não permaneceu aberta.'
            ipc('device','setFps','true');state=wait(lambda s:s['fps'])
            assert not state['message'],state['message']
            time.sleep(2);require_unlocked()
            subprocess.run(['timeout','8s','grim','/tmp/ilha-fps-metricas.png'],check=True)
            ipc('controlCenter','open','eDP-1');time.sleep(1)
            subprocess.run(['timeout','8s','grim','/tmp/ilha-monitor-control-center.png'],check=True)
            print('OK: métricas reais, desempenho/restauração, MangoHud OpenGL e capturas.')
    finally:
        ipc('controlCenter','close')
        ipc('device','setFps','true' if previous['fps'] else 'false')
        wait(lambda s:s['fps']==previous['fps'])
        ipc('device','setMetrics','true' if previous['metrics'] else 'false')
        ipc('device','setPerformance','true' if previous['controls'].get('performance') else 'false')
        wait(lambda s:bool(s['controls'].get('performance'))==bool(previous['controls'].get('performance')))
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,15);process.wait(timeout=3)


if __name__=='__main__':main()
