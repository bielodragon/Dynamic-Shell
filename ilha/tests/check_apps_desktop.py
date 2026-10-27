#!/usr/bin/env python3
"""Opt-in: prévias identificadas, catálogos e capturas; nunca inicia apps ou rede."""
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from app_events import Reporter
from check_launcher_desktop import require_unlocked


def ipc(target,method,*args):
    return subprocess.check_output(['/usr/bin/quickshell','-c','ilha','ipc','call',target,method,*args],text=True,timeout=5)


def capture(name):
    require_unlocked()
    subprocess.run(['grim', '/tmp/ilha-apps-'+name+'.png'],check=True,timeout=8)


def main():
    require_unlocked()
    assert not json.loads(ipc('launcher','status'))['present'],'Feche a pesquisa antes do teste.'
    reporters=[]
    try:
        for source,title,detail,progress in [('steam','Prévia Steam','Contadores locais de download',35),('localsend','Prévia LocalSend','CLI: progresso aproximado',50),('minecraft','Prévia Minecraft Java','Cliente inicializado',None)]:
            reporter=Reporter(source);reporters.append(reporter)
            reporter.emit(title,detail,progress=progress)
            time.sleep(2.3);capture(source)
            reporter.path.unlink(missing_ok=True);time.sleep(2.2)
        for source in ('steam','minecraft','localsend'):
            require_unlocked();ipc('launcher','open','');ipc('launcher','search','> '+source)
            time.sleep(.3);ipc('launcher','activate');time.sleep(.9)
            state=json.loads(ipc('launcher','status'))
            assert state['resultCount']>0 and not state['message'],state
            capture('pesquisa-'+source);ipc('launcher','close');time.sleep(.5)
        print('OK: três prévias e catálogos capturados. Sem iniciar jogos, apps ou transferências.')
    finally:
        ipc('launcher','close')
        for reporter in reporters:
            if reporter.path:reporter.path.unlink(missing_ok=True)
            ipc('activities','remove',reporter.id)


if __name__=='__main__':main()
