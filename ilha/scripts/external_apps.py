#!/usr/bin/env python3
"""Integração opcional com HyprMod; nunca instala nem modifica o Hyprland."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def perform(operation):
    executable = shutil.which('hyprmod')
    if operation == 'check': return {'available': bool(executable)}
    if operation != 'launch': raise ValueError('Operação desconhecida.')
    if not executable: raise ValueError('HyprMod não está instalado. Consulte o guia de configurações da Ilha.')
    directory = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'ilha'
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'hyprmod.log').open('a') as log:
        child = subprocess.Popen([executable], stdout=log, stderr=log, start_new_session=True)
        time.sleep(.3)
        if child.poll() not in (None, 0):
            raise RuntimeError('HyprMod não iniciou. Detalhes em ~/.cache/ilha/hyprmod.log.')
    return {'available': True}


if __name__ == '__main__':
    try: result = {'ok': True, **perform(sys.argv[1])}
    except (OSError, ValueError, RuntimeError, IndexError) as error: result = {'ok': False, 'error': str(error)}
    print(json.dumps(result, ensure_ascii=False))
