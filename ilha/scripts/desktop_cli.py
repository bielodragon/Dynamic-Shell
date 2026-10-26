#!/usr/bin/env python3
"""Controle da Ilha; nunca encerra processos de outros shells."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

QS = os.environ.get('ILHA_QUICKSHELL','/usr/bin/quickshell')


def command(args, check=True):
    return subprocess.run(args,capture_output=True,text=True,check=check,timeout=10)


def ipc(target, method, *args):
    return command([QS,'-c','ilha','ipc','call',target,method,*args]).stdout.strip()


def running():
    try: return json.loads(ipc('shell','status'))
    except (OSError, ValueError, subprocess.SubprocessError): return None


def start():
    if running(): return
    command([QS,'-c','ilha','-n','-d'])
    for _ in range(40):
        if running(): return
        time.sleep(.1)
    raise RuntimeError('A Ilha não iniciou. Consulte /usr/bin/quickshell -c ilha log -t 30.')


def focused():
    monitors = json.loads(command(['hyprctl','-j','monitors']).stdout)
    return next(item['name'] for item in monitors if item.get('focused'))


def clipboard():
    # Observadores anteriores são reutilizados; nunca encerrar processos alheios.
    if command(['pgrep','-u',str(os.getuid()),'-x','wl-paste'],check=False).returncode == 0: return
    import shutil
    if not all(shutil.which(name) for name in ('wl-paste','cliphist')): return
    for kind in ('text','image'):
        subprocess.Popen(['wl-paste','--type',kind,'--watch','cliphist','store'],start_new_session=True,
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description='Controla o shell Ilha sem remover Caelestia/Omarchy.')
    parser.add_argument('action', choices=['start','stop','toggle','reload','status','island-toggle','launcher','settings','setup','bars','sync'])
    parser.add_argument('--apply',action='store_true',help='Aplica a configuração preparada com backup.')
    parser.add_argument('--hide',action='store_true')
    parser.add_argument('--restore',action='store_true')
    args = parser.parse_args()
    try:
        from desktop_setup import conflicts, prepare_hyprland, bars
        if args.action == 'setup':
            # Sem --apply apenas mostra o bloco completo para revisão.
            result = prepare_hyprland(args.apply)
            result['otherShells'] = conflicts()
            print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
        if args.action == 'bars':
            print(json.dumps(bars(args.hide,args.restore),ensure_ascii=False,indent=2)); return 0
        runtime = Path(os.environ.get('XDG_RUNTIME_DIR','/tmp')) / ('ilha-' + str(os.getuid()))
        runtime.mkdir(mode=0o700,parents=True,exist_ok=True)
        with (runtime / 'lifecycle.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if args.action == 'status':
                print(json.dumps({'shell':running(),'otherShells':conflicts()},ensure_ascii=False)); return 0
            if args.action in ('stop','toggle','reload'):
                was_running = bool(running())
                if was_running:
                    command([QS,'-c','ilha','kill'])
                    for _ in range(30):
                        if not running(): break
                        time.sleep(.1)
                if args.action == 'stop' or args.action == 'toggle' and was_running: return 0
            start()
            if args.action in ('start','reload','toggle'): clipboard()
            elif args.action == 'island-toggle': ipc('shell','toggleIsland')
            elif args.action == 'launcher':
                ipc('ilha.'+focused(),'openLauncher')
            elif args.action == 'settings': ipc('settings','open','modules')
            elif args.action == 'sync': ipc('theme-sync','apply')
        return 0
    except (OSError, ValueError, RuntimeError, StopIteration, subprocess.SubprocessError) as error:
        print('Ilha: '+str(error),file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
