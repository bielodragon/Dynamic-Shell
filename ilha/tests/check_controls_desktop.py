#!/usr/bin/env python3
"""Opt-in: verifica Escape e sliders na sessão real, restaurando volume e brilho."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import system_controls as controls


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=10).stdout.strip()


def ipc(method, *args):
    for _ in range(25):
        value = command('/usr/bin/quickshell', '-c', 'ilha', 'ipc', 'call', 'controlCenter', method, *args)
        if method != 'status' or value.startswith('{'): return value
        time.sleep(.2)
    raise RuntimeError('IPC não ficou disponível após o reload.')


def main():
    before_audio, before_light = controls.audio(), controls.brightness()
    before_theme = command('/usr/bin/quickshell', '-c', 'ilha', 'ipc', 'call', 'ilha.eDP-1', 'getTheme')
    assert before_theme, 'Tema atual não foi lido; teste não iniciado.'
    try:
        ipc('open', 'eDP-1')
        time.sleep(.8)
        command('wtype', '-k', 'Escape')
        time.sleep(.4)
        assert not json.loads(ipc('status'))['opened'], 'Escape não fechou o painel.'
        ipc('open', 'eDP-1'); time.sleep(.8)
        command('wtype', '-k', 'Tab', '-k', 'Right')
        time.sleep(.8)
        actual = controls.audio()['volume']
        assert actual == min(100, before_audio['volume'] + 1), f'Slider volume: {actual}'
        ipc('close'); time.sleep(.4)
        ipc('open', 'eDP-1'); time.sleep(.8)
        command('wtype', '-k', 'Tab', '-k', 'Tab', '-k', 'Left')
        time.sleep(.8)
        actual = controls.brightness()['value']
        # O arredondamento do driver pode representar o passo de 1% com 1–2 pontos.
        assert 0 < before_light['value'] - actual <= 2, f'Slider brilho: {actual}'
        for theme in ('light', 'oled'):
            command('/usr/bin/quickshell', '-c', 'ilha', 'ipc', 'call', 'ilha.eDP-1', 'setTheme', theme)
            time.sleep(.7)
            ipc('open', 'eDP-1'); time.sleep(.5)
            command('grim', '/tmp/ilha-control-center-' + theme + '.png')
        print('OK: Escape, sliders por teclado e capturas claro/OLED; estados originais restaurados no finally.')
    finally:
        ipc('close')
        controls.action('volume', before_audio['volume'])
        controls.action('brightness', before_light['value'])
        command('/usr/bin/quickshell', '-c', 'ilha', 'ipc', 'call', 'ilha.eDP-1', 'setTheme', before_theme)


if __name__ == '__main__': main()
