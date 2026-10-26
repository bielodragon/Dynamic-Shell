#!/usr/bin/env python3
"""Opt-in: digitação/navegação/Escape reais, sem lançar apps, comandos ou copiar histórico."""
import json
import subprocess
import time


def command(*args):
    if args[0] == 'wtype': require_unlocked()
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=10).stdout.strip()


def require_unlocked():
    hint = subprocess.run(['loginctl','show-session','self','-p','LockedHint','--value'], capture_output=True,text=True,timeout=3)
    monitors = subprocess.run(['hyprctl','-j','monitors'], capture_output=True,text=True,timeout=3)
    data = json.loads(monitors.stdout)
    if hint.stdout.strip() == 'yes' or any('LOCK' in monitor.get('solitaryBlockedBy', []) or not monitor.get('dpmsStatus', False) for monitor in data):
        raise RuntimeError('Sessão bloqueada ou monitor desligado; teste gráfico não executado.')


def ipc(method, *args):
    return command('/usr/bin/quickshell','-c','ilha','ipc','call','launcher',method,*args)


def status(): return json.loads(ipc('status'))


def wait_for(predicate):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        try: current = status()
        except ValueError:
            time.sleep(.1)
            continue
        if predicate(current): return current
        time.sleep(.1)
    raise AssertionError('Launcher não chegou ao estado esperado.')


def main():
    require_unlocked()
    previous = command('/usr/bin/quickshell','-c','ilha','ipc','call','ilha.eDP-1','getTheme')
    assert previous
    try:
        command('/usr/bin/quickshell','-c','ilha','ipc','call','ilha.eDP-1','openLauncher')
        time.sleep(.8)
        command('wtype','firefox')
        wait_for(lambda s: s['mode']=='apps' and s['resultCount']>0)
        command('grim','/tmp/ilha-launcher-busca.png')
        command('wtype','-M','ctrl','-k','a','-m','ctrl','= sqrt(144)+2')
        wait_for(lambda s: s['calculatorResult']=='14')
        command('grim','/tmp/ilha-launcher-calculadora.png')
        command('wtype','-k','Down','-k','Up')
        assert status()['selectedIndex']==0
        for theme in ('light','oled'):
            command('/usr/bin/quickshell','-c','ilha','ipc','call','ilha.eDP-1','setTheme',theme)
            time.sleep(.6)
            command('grim','/tmp/ilha-launcher-'+theme+'.png')
        command('wtype','-k','Escape')
        wait_for(lambda s: not s['present'])
        layers = command('hyprctl','-j','layers')
        assert 'ilha-launcher' not in layers and 'ilha-island' in layers
        print('OK: digitação real, busca, cálculo, navegação, temas, Escape e retorno da ilha. Nenhuma ação executada.')
    finally:
        ipc('close')
        command('/usr/bin/quickshell','-c','ilha','ipc','call','ilha.eDP-1','setTheme',previous)


if __name__ == '__main__': main()
