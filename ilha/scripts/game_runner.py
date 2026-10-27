#!/usr/bin/env python3
"""Inicia um jogo com HUD da Ilha; comandos são argumentos, nunca shell."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import uuid
from theme_store import snapshot, write_json


def registry():
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime: raise RuntimeError('Sessão gráfica indisponível.')
    path = Path(runtime)/'ilha/games';path.mkdir(parents=True,exist_ok=True)
    return path


def sessions():
    rows = []
    for path in registry().glob('*.json'):
        try:
            data = json.loads(path.read_text())
            # Não tocar em sockets de jogos iniciados por outro usuário/processo.
            if not (Path('/proc')/str(data['runnerPid'])).exists():
                path.unlink();continue
            rows.append((path,data))
        except (OSError,ValueError,KeyError): continue
    return rows


def set_visible(value):
    if type(value) is not bool: raise ValueError('FPS exige ligado/desligado.')
    errors = []
    for path, data in sessions():
        if data['visible'] == value: continue
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                client.settimeout(1)
                client.connect('\0'+data['socket'])
                # Aguardar identificação confirma que o jogo aceitou o cliente.
                if not client.recv(2048): raise RuntimeError('O jogo não respondeu ao HUD.')
                client.sendall(b':hud;')
            data['visible'] = value;write_json(path,data)
        except (OSError,RuntimeError) as error: errors.append(str(error))
    if errors: raise RuntimeError('HUD: '+errors[0])


def options(theme, visible, name):
    colors = theme['colors']
    # Não mostrar zeros de GPU em drivers sem suporte. Sensores validados ficam no overlay da Ilha.
    result = ['fps','frametime','cpu_stats','cpu_temp','ram','gpu_stats=0','gpu_temp=0','vram=0',
        'control='+name,'position=top-left','offset_y=80','font_size=20','background_alpha='+str(theme['glassOpacity'])]
    for key, token in [('text_color','text'),('background_color','background'),('cpu_color','accent'),
                       ('gpu_color','success'),('ram_color','secondaryText'),('vram_color','warning'),('frametime_color','accent'),
                       ('engine_color','accent')]:
        result.append(key+'='+colors[token].lstrip('#'))
    if not visible: result.append('no_display')
    return ','.join(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opengl',action='store_true',help='Usa a interposição OpenGL --dlsym do MangoHud.')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command and command[0]=='--': command=command[1:]
    if not command: parser.error('Informe o programa após --.')
    mango=shutil.which('mangohud')
    if not mango: parser.error('MangoHud não instalado; instale mangohud e, para jogos 32 bits, lib32-mangohud.')
    state=snapshot();theme=next(t for t in state['themes'] if t['id']==state['config']['theme'])
    accent=(state['config'].get('overrides') or {}).get('accent')
    if accent: theme['colors']['accent']=accent
    visible=bool(state['config'].get('monitoring',{}).get('fps',False))
    identifier=uuid.uuid4().hex;name='ilha-hud-'+str(os.getuid())+'-'+identifier
    env=dict(os.environ,MANGOHUD_CONFIG=options(theme,visible,name))
    record=registry()/(identifier+'.json')
    child=subprocess.Popen([mango]+(['--dlsym'] if args.opengl else [])+command,env=env)
    appid=os.environ.get('SteamAppId','')
    metadata={'steamAppId':appid} if appid.isdigit() and 0<int(appid)<10000000000 else {}
    write_json(record,{'runnerPid':os.getpid(),'pid':child.pid,'socket':name,'visible':visible,**metadata})
    def forward(signum, frame):
        if child.poll() is None: child.send_signal(signum)
    signal.signal(signal.SIGTERM,forward);signal.signal(signal.SIGINT,forward)
    try: return child.wait()
    finally: record.unlink(missing_ok=True)


if __name__=='__main__': raise SystemExit(main())
