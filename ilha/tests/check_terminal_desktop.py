#!/usr/bin/env python3
"""Opt-in: comando próprio real → observador → atividade QML; sem instalação de pacotes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from check_launcher_desktop import require_unlocked
ROOT=Path(__file__).resolve().parents[1]


def activities():
    result=subprocess.check_output(['/usr/bin/quickshell','-c','ilha','ipc','call','activities','list'],text=True,timeout=4)
    return json.loads(result)['activities']


def main():
    require_unlocked();path=None;identifier=None
    process=subprocess.Popen([sys.executable,str(ROOT/'scripts/terminal_activity.py'),'--title','Teste do terminal',
        '--',sys.executable,'-c','import time;time.sleep(5)'])
    try:
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            for candidate in (Path(os.environ['XDG_RUNTIME_DIR'])/'ilha/app-activities').glob('*.json'):
                try:
                    event=json.loads(candidate.read_text())
                    if event['source']=='terminal' and event['pid']==process.pid:path=candidate;identifier=event['activity']['id']
                except (OSError,ValueError,KeyError):pass
            if identifier and any(row['id']==identifier and row['state']=='running' and row['progress'] is None for row in activities()):break
            time.sleep(.1)
        else:raise AssertionError('Comando não apareceu na Ilha.')
        require_unlocked();subprocess.run(['grim','/tmp/ilha-terminal-atividade.png'],check=True,timeout=8)
        assert process.wait(timeout=7)==0
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            if any(row['id']==identifier and row['state']=='success' for row in activities()):break
            time.sleep(.1)
        else:raise AssertionError('Conclusão não apareceu.')
        print('OK: comando real, estado running indeterminado, conclusão e captura. Sem alterar pacotes ou shell.')
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=5)
        if path:path.unlink(missing_ok=True)
        if identifier:subprocess.run(['/usr/bin/quickshell','-c','ilha','ipc','call','activities','remove',identifier],capture_output=True,timeout=4)


if __name__=='__main__':main()
