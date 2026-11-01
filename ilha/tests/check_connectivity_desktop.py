#!/usr/bin/env python3
"""Opt-in: lista adaptadores reais e captura painéis; nunca conecta/desconecta/busca."""
import json
import subprocess
import time
from check_launcher_desktop import require_unlocked


def ipc(target,method,*args):
    return subprocess.check_output(['/usr/bin/quickshell','-c','ilha','ipc','call',target,method,*args],text=True,timeout=5)


def main():
    require_unlocked()
    previous=json.loads(ipc('controlCenter','status'))
    if previous['opened']:raise RuntimeError('Control Center já está aberto; feche antes do teste opt-in.')
    monitors=json.loads(subprocess.check_output(['hyprctl','-j','monitors'],text=True))
    screen=next(row['name'] for row in monitors if row.get('focused'))
    try:
        ipc('controlCenter','open',screen);time.sleep(.5)
        for mode in ('wifi','bluetooth'):
            require_unlocked();ipc('connectivity','open',mode)
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                state=json.loads(ipc('connectivity','status'))
                if state['mode']==mode and state['ready'] and 'available' in state['state']:break
                time.sleep(.1)
            else:raise AssertionError('Painel não carregou: '+str(state.get('message')))
            time.sleep(.4);require_unlocked()
            subprocess.run(['grim','/tmp/ilha-conectividade-'+mode+'.png'],check=True,timeout=8)
            print(mode+': painel carregado, sem comandos de rádio/conexão.')
    finally:
        ipc('connectivity','back');ipc('controlCenter','close')
    print('OK: painéis layer-shell e capturas; sessão/rede/dispositivos preservados.')


if __name__=='__main__':main()
