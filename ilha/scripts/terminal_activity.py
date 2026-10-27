#!/usr/bin/env python3
"""Acompanha um comando explícito, sem interceptar stdin/stdout/stderr."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
from app_events import Reporter


def title_for(command):
    # Somente nomes conhecidos; argumentos, destinos e credenciais nunca viram título.
    name=Path(command[0]).name
    if name=='sudo' and len(command)>1:name=Path(command[1]).name
    return {'pacman':'Pacman em execução','yay':'Yay em execução','make':'Build em execução',
        'ninja':'Build em execução','cargo':'Cargo em execução','npm':'npm em execução',
        'pnpm':'pnpm em execução'}.get(name,'Comando no terminal')


def run(command,title=None):
    if os.geteuid()==0:raise ValueError('Execute ilha-run como usuário; coloque sudo depois de -- quando necessário.')
    reporter=Reporter('terminal');title=title or title_for(command)
    reporter.emit(title,'Executando; progresso indeterminado')
    child=None;handlers={}
    try:
        # O filho herda os três descritores e o terminal. Nenhum byte é lido pelo wrapper.
        child=subprocess.Popen(command)
        def forward(signum,_):
            if child.poll() is None:child.send_signal(signum)
        for sig in (signal.SIGTERM,signal.SIGHUP):handlers[sig]=signal.signal(sig,forward)
        # Ctrl+C do terminal já alcança o grupo do filho. Não interromper o wait do wrapper.
        handlers[signal.SIGINT]=signal.signal(signal.SIGINT,lambda *_:None)
        while True:
            try:result=child.wait(timeout=2);break
            except subprocess.TimeoutExpired:reporter.emit(title,'Executando; progresso indeterminado')
        interrupted=result<0 or result in (130,137,143)
        reporter.emit(title,'Processo interrompido' if interrupted else 'Comando concluído' if result==0 else 'Comando terminou com erro',
            state='paused' if interrupted else 'success' if result==0 else 'error',final=True)
        return result if result>=0 else 128-result
    except OSError:
        reporter.emit(title,'Não foi possível executar o comando',state='error',final=True)
        print('Não foi possível executar o comando solicitado.',file=sys.stderr);return 127
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title',help='Título explícito; não inclua informações privadas.')
    parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
    command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Informe o comando depois de --.')
    if args.title is not None and not 1<=len(args.title.strip())<=120:parser.error('Título deve ter de 1 a 120 caracteres.')
    try:return run(command,args.title)
    except ValueError as error:print(str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
