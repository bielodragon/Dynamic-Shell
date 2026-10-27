#!/usr/bin/env python3
"""Planeja dependências Arch sem rede; --apply exige confirmação no terminal."""
import argparse
from dataclasses import dataclass
import json
import os
import re
import shlex
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class Requirement:
    name: str
    alternatives: tuple=()
    commands: tuple=()
    aur: str=''
    minimum: str=''


R=Requirement
MODULES={
    'core':('Ilha, fonte, Hyprland e serviços Python/QML',[
        R('python'),R('hyprland'),R('quickshell',minimum='0.3.1'),R('qt6-wayland'),R('qt6-svg'),R('qt6-websockets'),
        R('python-dbus'),R('python-gobject'),R('procps-ng'),R('ttf-jetbrains-mono-nerd',alternatives=('ttf-jetbrains-mono-nerd-basic',))]),
    'audio':('Áudio e observação PipeWire',[R('pipewire'),R('wireplumber')]),
    'controls':('Wi-Fi, Bluetooth, brilho e perfis',[R('networkmanager'),R('bluez'),R('bluez-utils'),R('brightnessctl'),R('power-profiles-daemon'),R('upower')]),
    'launcher':('Clipboard e abertura de terminal',[R('wl-clipboard'),R('cliphist'),R('xdg-terminal-exec'),R('foot',alternatives=('kitty','alacritty','ghostty','konsole'))]),
    'phone':('KDE Connect',[R('kdeconnect')]),
    'wallpaper':('Vídeo/GIF nativo',[R('qt6-multimedia'),R('qt6-multimedia-ffmpeg'),R('ffmpeg')]),
    'static-wallpaper':('Provedor estático, quando não houver outro',[R('awww',alternatives=('swww',),commands=('caelestia','awww','swww'))]),
    'lock':('Bloqueio; ainda exige configuração do usuário',[R('hyprlock',alternatives=('swaylock',),commands=('caelestia','hyprlock','swaylock'))]),
    'sync':('Preferência claro/escuro; Kitty opcional',[R('gsettings-desktop-schemas'),R('glib2')]),
    'fps':('MangoHud para jogos 64 bits',[R('mangohud')]),
    'fps32':('MangoHud 32 bits; requer multilib habilitado',[R('lib32-mangohud')]),
    'steam':('Aplicativo Steam; requer multilib',[R('steam',commands=('steam',))]),
    'minecraft':('Prism Launcher; não instala jogos/mods',[R('prismlauncher',commands=('prismlauncher',))]),
    'localsend':('LocalSend; CLI depende do pacote/versão',[R('localsend',commands=('localsend',),aur='localsend-bin')]),
    'vscodium':('Editor compatível via CLI codium',[R('vscodium',commands=('codium',),aur='vscodium-bin')]),
    'vscode':('Editor compatível via CLI code',[R('visual-studio-code-bin',commands=('code',),aur='visual-studio-code-bin')]),
    'dev':('Git, testes JS e capturas opcionais',[R('git'),R('nodejs'),R('grim'),R('wtype')]),
}
PROFILES={
    'minimal':('core',),
    'desktop':('core','audio','controls','launcher','wallpaper','static-wallpaper','lock','sync'),
    'full':('core','audio','controls','launcher','phone','wallpaper','static-wallpaper','lock','sync','fps'),
}
OFFICIAL={'core','extra','multilib','core-testing','extra-testing','multilib-testing','gnome-unstable','kde-unstable'}
ENV={**os.environ,'LC_ALL':'C'}


def run_read(args):
    return subprocess.run(args,capture_output=True,text=True,env=ENV,timeout=12)


def satisfied(requirement):
    for name in (requirement.name,*requirement.alternatives):
        dependency=name+('>='+requirement.minimum if requirement.minimum else '')
        if run_read(['pacman','-T','--',dependency]).returncode==0:return name
    # Preservar instalações alternativas compatíveis. A versão QML precisa ser conferida.
    for command in requirement.commands:
        if shutil.which(command):return command+' (comando existente)'
    if requirement.name=='quickshell' and os.path.isfile('/usr/bin/quickshell'):
        result=run_read(['/usr/bin/quickshell','--version']);match=re.search(r'(\d+)\.(\d+)\.(\d+)',result.stdout)
        if result.returncode==0 and match and tuple(map(int,match.groups()))>=(0,3,1):return 'quickshell (binário compatível)'
    return ''


def repository(name,minimum=''):
    result=run_read(['pacman','-Si','--',name])
    if result.returncode:return None
    # pacman imprime primeiro o repositório com prioridade efetiva.
    fields={}
    for line in result.stdout.split('\n\n')[0].splitlines():
        if ':' in line:
            key,value=line.split(':',1);fields[key.strip()]=value.strip()
    if not all(fields.get(key) for key in ('Repository','Name','Version')):return None
    if minimum and run_read(['vercmp',fields['Version'],minimum]).stdout.strip().startswith('-'):return None
    return {'repository':fields['Repository'],'package':fields['Name'],'version':fields['Version']}


def plan(modules,allow_aur=False,helper='auto'):
    if not shutil.which('pacman'):raise ValueError('Este instalador de dependências requer Arch Linux/pacman.')
    chosen=list(dict.fromkeys(['core',*modules]));unknown=set(chosen)-set(MODULES)
    if unknown:raise ValueError('Módulo desconhecido: '+', '.join(sorted(unknown)))
    result={'modules':chosen,'installed':[],'repositories':[],'aur':[],'blocked':[]}
    seen=set()
    for module in chosen:
        for requirement in MODULES[module][1]:
            if requirement.name in seen:continue
            seen.add(requirement.name)
            present=satisfied(requirement)
            if present:result['installed'].append({'dependency':requirement.name,'provider':present});continue
            found=None
            for name in (requirement.name,*requirement.alternatives):
                found=repository(name,requirement.minimum)
                if found:break
            if found:
                found['official']=found['repository'] in OFFICIAL;result['repositories'].append(found)
            elif requirement.aur:
                result['aur'].append(requirement.aur)
                if not allow_aur:result['blocked'].append('AUR desativado: '+requirement.aur+' (revise e use --allow-aur).')
            else:result['blocked'].append('Sem pacote compatível no banco local: '+requirement.name+(' (habilite multilib manualmente, se necessário).' if requirement.name in ('steam','lib32-mangohud') else '.'))
    selected=next((command for command in (('yay','paru') if helper=='auto' else (helper,)) if shutil.which(command)),None)
    if result['aur'] and allow_aur:
        for name in ('base-devel','git'):
            if name in seen:continue
            present=satisfied(R(name))
            if present:result['installed'].append({'dependency':name,'provider':present});continue
            found=repository(name)
            if found:
                found['official']=found['repository'] in OFFICIAL;result['repositories'].append(found)
            else:result['blocked'].append('Dependência de build AUR indisponível: '+name)
    if result['aur'] and allow_aur and not selected:result['blocked'].append('Instale/revise um helper yay ou paru como usuário antes de usar AUR.')
    result['helper']=selected
    # Na máquina Omarchy usar seu comando público; Arch puro usa pacman diretamente.
    result['manager']='omarchy' if shutil.which('omarchy') else 'pacman'
    return result


def commands_for(result):
    commands=[]
    if result['repositories']:
        packages=[row['package'] for row in result['repositories']]
        commands.append((['omarchy','pkg','add'] if result['manager']=='omarchy' else ['sudo','pacman','-S','--needed','--'])+packages)
    if result['aur'] and result['helper']:commands.append([result['helper'],'-S','--aur','--needed','--',*result['aur']])
    return commands


def display(result):
    print('Módulos: '+', '.join(result['modules']))
    print('Já atendidas: '+(', '.join(row['provider'] for row in result['installed']) or 'nenhuma'))
    for row in result['repositories']:
        print(('Arch oficial' if row['official'] else 'Repositório adicional')+': '+row['repository']+'/'+row['package']+' '+row['version'])
    for package in result['aur']:print('AUR (PKGBUILD a revisar, versão não consultada): '+package)
    for reason in result['blocked']:print('Pendente: '+reason)
    for command in commands_for(result):print('Comando proposto: '+shlex.join(command))
    if result['manager']=='omarchy' and result['repositories']:print('O backend Omarchy usa --noconfirm internamente; confirme a lista/transação abaixo antes de continuar.')
    print('Não sincroniza bancos, não atualiza o sistema inteiro e não habilita serviços, multilib ou drivers.')


def apply(result):
    if os.geteuid()==0:raise ValueError('Execute sem sudo. Apenas a etapa de pacman eleva privilégios; AUR nunca roda como root.')
    if result['blocked']:raise ValueError('Resolva as pendências antes de instalar; nenhum pacote foi alterado.')
    if not result['repositories'] and not result['aur']:print('Todas as dependências selecionadas já estão atendidas.');return
    if not sys.stdin.isatty():raise ValueError('--apply requer um terminal para revisar e confirmar; não há confirmação automática.')
    if result['repositories']:
        # Resolver e mostrar a transação antes da confirmação, sem instalar ou baixar.
        preview=run_read(['pacman','-Sp','--print-format','%r/%n %v (%s bytes)','--',*[row['package'] for row in result['repositories']]])
        if preview.returncode:raise ValueError('Não foi possível resolver a transação. Revise pacman/mirrors manualmente. '+preview.stderr.strip()[:300])
        print('Transação resolvida (inclui dependências):\n'+preview.stdout)
    if input('Instalar os pacotes mostrados? [s/N] ').strip().lower() not in ('s','sim'):print('Cancelado.');return
    for command in commands_for(result):
        if command[0] in ('yay','paru'):
            if os.geteuid()==0:raise ValueError('AUR não pode rodar como root.')
            if input('Continuar para a revisão e instalação separada do AUR? [s/N] ').strip().lower() not in ('s','sim'):
                print('Etapa AUR cancelada; pacotes de repositório eventualmente instalados foram mantidos.');return
        subprocess.run(command,check=True)
    print('Pacotes solicitados instalados. Serviços e aplicativos ainda precisam da configuração da sessão; consulte DEPENDENCIAS.md.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=PROFILES,default='desktop')
    parser.add_argument('--modules',default='',help='Módulos adicionais separados por vírgula.')
    parser.add_argument('--list',action='store_true',help='Lista perfis e módulos sem consultar pacman.')
    parser.add_argument('--json',action='store_true',help='Prévia estruturada, sem mensagens ou instalação.')
    parser.add_argument('--dry-run',action='store_true',help='Prévia (padrão).')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--allow-aur',action='store_true')
    parser.add_argument('--aur-helper',choices=['auto','yay','paru'],default='auto')
    args=parser.parse_args()
    try:
        if args.list:
            for name,modules in PROFILES.items():print(name+': '+', '.join(modules))
            for name,(description,_) in MODULES.items():print(name+': '+description)
            return 0
        if args.apply and (args.json or args.dry_run):raise ValueError('Use --apply separado de --dry-run/--json.')
        modules=[*PROFILES[args.profile],*[part.strip() for part in args.modules.split(',') if part.strip()]]
        result=plan(modules,args.allow_aur,args.aur_helper)
        if args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
        else:display(result)
        if args.apply:apply(result)
        return 0
    except (OSError,ValueError,subprocess.SubprocessError,EOFError,KeyboardInterrupt) as error:
        print('Dependências: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
