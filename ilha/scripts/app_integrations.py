#!/usr/bin/env python3
"""Catálogos, abertura e observação das integrações locais."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from app_sources import steam_games,instances,DownloadTracker
from app_events import read_events


def catalog(source):
    if source not in ('steam','minecraft','localsend'):raise ValueError('Integração desconhecida.')
    names={'steam':'Steam','minecraft':'Prism Launcher','localsend':'LocalSend'}
    commands={'steam':'steam','minecraft':'prismlauncher','localsend':'localsend'}
    rows=[{'kind':'integration-open','source':source,'id':'client','title':'Abrir '+names[source],
        'detail':'Aplicativo disponível' if shutil.which(commands[source]) else 'Não instalado',
        'icon':{'steam':'steam','minecraft':'org.prismlauncher.PrismLauncher','localsend':'localsend'}[source]}]
    if source=='steam':
        rows += [{'kind':'steam-game','source':source,'id':g['id'],'title':g['name'],'detail':'Jogar pela Steam','icon':'steam'} for g in steam_games()]
    elif source=='minecraft':
        rows += [{'kind':'minecraft-instance','source':source,'id':g['id'],'title':g['name'],'detail':'Instância do Prism Launcher','icon':'org.prismlauncher.PrismLauncher'} for g in instances()]
    else:
        rows += [{'kind':'integration-open','source':source,'id':'cli','title':'Transferências na Ilha — LocalSend CLI',
            'detail':'Escolha o dispositivo e confirme no terminal','icon':'utilities-terminal'}]
    return rows


def launch(source,identifier='client'):
    if source=='steam':
        executable=shutil.which('steam')
        if not executable:raise ValueError('Steam não instalada.')
        args=[executable]
        if identifier!='client':
            if not any(g['id']==identifier for g in steam_games()):raise ValueError('Jogo não encontrado na biblioteca local.')
            args.append('steam://rungameid/'+identifier)
    elif source=='minecraft':
        executable=shutil.which('prismlauncher')
        if not executable:raise ValueError('Prism Launcher não instalado.')
        args=[executable]
        if identifier!='client':
            instance=next((row for row in instances() if row['id']==identifier),None)
            if not instance:raise ValueError('Instância não encontrada.')
            args += ['--dir',instance['root'],'--launch',instance['folder']]
    elif source=='localsend':
        if identifier=='cli':
            if not shutil.which('localsend-cli'):raise ValueError('LocalSend CLI não instalado.')
            terminal=shutil.which('xdg-terminal-exec') or shutil.which('foot') or shutil.which('kitty')
            if not terminal:raise ValueError('Terminal não encontrado.')
            args=[terminal,'python3',str(Path(__file__).with_name('localsend_activity.py'))]
        else:
            executable=shutil.which('localsend')
            if not executable:raise ValueError('LocalSend não instalado.')
            args=[executable]
    else:raise ValueError('Integração desconhecida.')
    subprocess.Popen(args,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def setup_minecraft(identifier,apply=False):
    instance=next((row for row in instances() if row['id']==identifier),None)
    if not instance:raise ValueError('Instância não encontrada.')
    path=Path(instance['config']);text=path.read_text()
    # Wrapper global também precisa ser preservado.
    global_path=Path(instance['root'])/'prismlauncher.cfg'
    global_text=global_path.read_text() if global_path.exists() else ''
    wrapper=Path.home()/'.local/bin/ilha-minecraft'
    if not wrapper.exists():wrapper=Path('/usr/local/bin/ilha-minecraft')
    if not wrapper.exists():raise ValueError('Execute o instalador da Ilha para criar ilha-minecraft.')
    command='"'+str(wrapper).replace('"','\\"')+'"'
    for content in (text,global_text):
        for key in ('WrapperCommand','PreLaunchCommand','PostExitCommand'):
            match=re.search(r'^'+key+r'=(.*)$',content,re.M)
            value=match.group(1).strip() if match else ''
            if value and not (key=='WrapperCommand' and value in (command,str(wrapper))):
                raise ValueError('Há comandos personalizados no Prism; revise a composição antes de substituir.')
    updated=text
    for key,value in [('OverrideCommands','true'),('WrapperCommand',command)]:
        if re.search(r'^'+key+r'=.*$',updated,re.M):updated=re.sub(r'^'+key+r'=.*$',lambda _:key+'='+value,updated,flags=re.M)
        else:updated=updated.replace('[General]','[General]\n'+key+'='+value,1)
    result={'instance':instance['name'],'path':str(path),'wrapper':command,'dryRun':not apply}
    if apply and updated!=text:
        backup=Path(str(path)+'.bak.ilha-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        shutil.copy2(path,backup);path.write_text(updated);result['backup']=str(backup)
    return result


def monitor(enabled):
    tracker=DownloadTracker()
    while True:
        rows=read_events(enabled)
        if enabled.get('steam',True):
            running=subprocess.run(['pgrep','-u',str(os.getuid()),'-x','steam'],capture_output=True).returncode==0
            games=steam_games();rows+=tracker.sample(games,running,time.monotonic())
            # Jogos iniciados pelo wrapper já usado para MangoHud expõem apenas AppID, nunca env completo.
            from game_runner import sessions
            names={g['id']:g['name'] for g in games}
            for path,game in sessions():
                appid=game.get('steamAppId')
                if appid:rows.append({'id':'steam:game:'+path.stem,'app':'Steam','title':names.get(appid,'Jogo Steam '+appid),
                    'detail':'Em execução','state':'running','progress':None,'ttl':12})
        print(json.dumps({'activities':rows[:12]},ensure_ascii=False),flush=True)
        time.sleep(2)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='operation',required=True)
    listing=sub.add_parser('list');listing.add_argument('source',choices=['steam','minecraft','localsend'])
    opening=sub.add_parser('launch');opening.add_argument('source',choices=['steam','minecraft','localsend']);opening.add_argument('id',nargs='?',default='client')
    watching=sub.add_parser('monitor');watching.add_argument('sources')
    setup=sub.add_parser('setup-minecraft');setup.add_argument('id');setup.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:
        if args.operation=='monitor':monitor(json.loads(args.sources));return 0
        if args.operation=='list':result={'rows':catalog(args.source)}
        elif args.operation=='launch':launch(args.source,args.id);result={}
        else:result=setup_minecraft(args.id,args.apply)
        print(json.dumps({'ok':True,**result},ensure_ascii=False));return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(json.dumps({'ok':False,'error':str(error)[:240]},ensure_ascii=False));return 1


if __name__=='__main__':raise SystemExit(main())
