"""Efeitos de compositor reversíveis; não altera drivers/clocks ou arquivos Hyprland."""
import json
import os
from pathlib import Path
import subprocess
from theme_store import write_json

OPTIONS = ('decoration:blur:enabled','animations:enabled','decoration:shadow:enabled')


def state_path():
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    signature = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if not runtime or not signature: raise RuntimeError('Modo de desempenho exige uma sessão Hyprland ativa.')
    return Path(runtime)/'ilha'/('performance-'+signature+'.json')


def read(name):
    result = subprocess.run(['hyprctl','-j','getoption',name],capture_output=True,text=True,timeout=3,check=True)
    data = json.loads(result.stdout)
    value = data.get('bool',data.get('int'))
    if type(value) not in (bool,int): raise RuntimeError('Opção de efeito não suportada: '+name)
    return bool(value)


def set_option(name,value):
    result = subprocess.run(['hyprctl','keyword',name,'true' if value else 'false'],capture_output=True,text=True,timeout=3)
    if 'non-legacy parsers' in result.stdout + result.stderr:
        expression = 'hl.config({ ['+json.dumps(name.replace(':','.'))+'] = '+('true' if value else 'false')+' })'
        result = subprocess.run(['hyprctl','eval',expression],capture_output=True,text=True,timeout=3,check=True)
    if result.returncode or result.stdout.strip() not in ('ok',''):
        raise RuntimeError(result.stdout.strip() or result.stderr.strip())


def enabled():
    try: return state_path().exists()
    except RuntimeError: return False


def apply(value):
    if type(value) is not bool: raise ValueError('Desempenho exige ligado/desligado.')
    path = state_path()
    if value:
        if path.exists(): return
        previous = {name:read(name) for name in OPTIONS}
        # Salvar antes de mudar permite recuperar uma aplicação interrompida.
        write_json(path,previous)
        try:
            for name in OPTIONS: set_option(name,False)
        except Exception:
            apply(False);raise
    elif path.exists():
        previous = json.loads(path.read_text())
        for name in OPTIONS:
            # Uma alteração externa posterior tem prioridade.
            if not read(name): set_option(name,previous[name])
        path.unlink()
