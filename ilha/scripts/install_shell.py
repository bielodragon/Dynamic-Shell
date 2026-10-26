#!/usr/bin/env python3
"""Instala código e comandos. Configurações pessoais não são substituídas."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]


def install(mode, destdir=None, dry_run=False):
    root = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    target = root / 'quickshell/ilha' if mode == 'user' else Path('/etc/xdg/quickshell/ilha')
    binary = Path.home() / '.local/bin' if mode == 'user' else Path('/usr/local/bin')
    staged = lambda path: Path(destdir) / str(path).lstrip('/') if destdir else path
    result = {'mode':mode,'code':str(staged(target)),'commands':str(staged(binary)),
              'personalConfig':'preservada em $XDG_CONFIG_HOME/ilha', 'dryRun':dry_run}
    if dry_run: return result
    if mode == 'system' and not destdir and os.geteuid() != 0:
        raise ValueError('Execute sudo ./install-system.sh. Nenhuma configuração pessoal será escrita como root.')
    destination = staged(target)
    if destination.resolve() != SOURCE.resolve():
        if destination.exists():
            backup = Path(str(destination)+'.bak.ilha-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            destination.rename(backup); result['backup'] = str(backup)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(SOURCE,destination,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.log','.qmlls.ini'))
    staged(binary).mkdir(parents=True,exist_ok=True)
    for name, script in [('ilha','desktop_cli.py'),('ilha-activity','activity_cli.py')]:
        wrapper = staged(binary) / name
        if wrapper.exists() or wrapper.is_symlink():
            shutil.copy2(wrapper, str(wrapper)+'.bak.ilha-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            if wrapper.is_symlink(): wrapper.unlink()
        wrapper.write_text('#!/bin/sh\nexec python3 '+shlex.quote(str(target / 'scripts' / script))+' "$@"\n')
        wrapper.chmod(0o755)
    if mode == 'user':
        staged(Path.home() / 'Pictures/Wallpapers').mkdir(parents=True,exist_ok=True)
    return result


def dependencies():
    qs = Path('/usr/bin/quickshell')
    if not qs.exists(): raise ValueError('Falta quickshell >= 0.3.1. Instale-o antes de continuar; nenhum pacote foi instalado automaticamente.')
    version = subprocess.check_output([str(qs),'--version'],text=True,timeout=4)
    match = re.search(r'(\d+)\.(\d+)\.(\d+)',version)
    if not match or tuple(map(int,match.groups())) < (0,3,1): raise ValueError('É necessário Quickshell >= 0.3.1.')
    print('Quickshell:',version.strip())
    print('Pacotes para os módulos completos: python-dbus, python-gobject, qt6-websockets, pipewire, ttf-jetbrains-mono-nerd.')
    print('Integrações opcionais: networkmanager, bluez-utils, wireplumber, brightnessctl, power-profiles-daemon, kdeconnect, wl-clipboard, cliphist, kitty, hyprlock ou swaylock e Caelestia ou daemon awww/swww para wallpaper.')
    print('Nenhum pacote será instalado por este script. Consulte DEPENDENCIAS.md para as opções.')


def yes(question):
    return input(question+' [s/N] ').strip().casefold() in ('s','sim')


def main():
    parser = argparse.ArgumentParser(description='Instala a Ilha por usuário ou para o sistema; não apaga outros shells.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--user',action='store_true'); group.add_argument('--system',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--destdir',type=Path,help='Raiz de staging para testes/empacotamento, sem tocar na sessão.')
    parser.add_argument('--non-interactive',action='store_true',help='Somente copia; não ativa, altera Hyprland ou troca shells.')
    args = parser.parse_args()
    try:
        if args.user and os.geteuid() == 0 and not args.destdir and not args.dry_run:
            raise ValueError('Execute ./install.sh sem sudo para instalar só no seu usuário.')
        if not args.destdir: dependencies()
        result = install('user' if args.user else 'system',args.destdir,args.dry_run)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.destdir or args.dry_run: return 0
        if args.system:
            print('Cada usuário pode executar ilha setup para revisar e ilha setup --apply para habilitar atalhos/autostart. Configurações e temas continuam separados por usuário.')
            print('Configurações ~/.config/quickshell/ilha existentes têm prioridade sobre a instalação global; nada foi apagado.')
            return 0
        from desktop_setup import conflicts, prepare_hyprland, bars
        others = conflicts()
        if others: print('Possíveis conflitos:',', '.join(others),'. A Ilha não os encerra nem remove.')
        if not args.non_interactive and sys.stdin.isatty():
            print(json.dumps(prepare_hyprland(),ensure_ascii=False,indent=2))
            if yes('Quer usar a Ilha na sessão e aplicar estes atalhos/autostart, mantendo os outros shells instalados?'):
                print(prepare_hyprland(True))
                if 'Caelestia' in others and yes('Quer ocultar somente a barra e a sidebar do Caelestia, mantendo wallpaper, bloqueio e notificações dele?'):
                    print(bars(hide=True))
                subprocess.run(['python3',str(Path(result['code'])/'scripts/desktop_cli.py'),'start'],check=True)
        else: print('Instalado sem ativar. Execute ilha setup para revisar a integração com o Hyprland.')
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, EOFError) as error:
        print('Instalação: '+str(error),file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
