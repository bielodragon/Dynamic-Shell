#!/usr/bin/env python3
"""Wrapper para o Java do Prism; argumentos e logs não entram na atividade."""
import argparse
import os
from pathlib import Path
import sys
from app_events import Reporter
from app_streams import MinecraftParser
from activity_process import relay


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fps',action='store_true');parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Prism deve passar o comando Java ao wrapper.')
    reporter=Reporter('minecraft');reader=MinecraftParser()
    title=os.environ.get('INST_NAME','Minecraft Java')[:120]
    detail='Iniciando cliente'
    def output(data):
        nonlocal detail
        update=reader.feed(data)
        if update:detail=update;reporter.emit(title,detail)
    def heartbeat():reporter.emit(title,detail)
    if args.fps:command=[sys.executable,str(Path(__file__).with_name('game_runner.py')),'--opengl','--']+command
    try:
        reporter.emit(title,detail);result=relay(command,output,heartbeat)
        reporter.emit(title,'Sessão encerrada' if result==0 else 'Processo interrompido' if result<0 else 'O jogo terminou com erro',
            state='success' if result==0 else 'paused' if result<0 else 'error',final=True)
        return result if result>=0 else 128-result
    except (OSError,ValueError) as error:
        reporter.emit(title,'Não foi possível iniciar o jogo',state='error',final=True)
        print(str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
