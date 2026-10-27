#!/usr/bin/env python3
"""Ponte local NDJSON para eventos públicos do editor; não aceita comandos."""
import argparse
import json
import re
import select
import sys
import time
from app_events import Reporter

KINDS={'task':('Tarefa','Tarefa em execução'),'debug':('Depuração','Sessão de depuração ativa'),
    'terminal':('Terminal integrado','Comando em execução')}


class Bridge:
    def __init__(self,app):self.app={'vscode':'VS Code','vscodium':'VSCodium'}[app];self.entries={}
    def receive(self,event):
        if not isinstance(event,dict):raise ValueError('Evento inválido.')
        key=event.get('id','');operation=event.get('op');kind=event.get('kind')
        if not isinstance(key,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',key):raise ValueError('ID inválido.')
        if operation=='start':
            if kind not in KINDS:raise ValueError('Tipo inválido.')
            if key in self.entries:return
            if len(self.entries)>=8:raise ValueError('Limite de atividades do editor atingido.')
            reporter=Reporter('editors');title=self.app+' · '+KINDS[kind][0]
            self.entries[key]=(reporter,title,kind);reporter.emit(title,KINDS[kind][1])
        elif operation=='end':
            entry=self.entries.pop(key,None)
            if not entry:return
            reporter,title,kind=entry;code=event.get('exitCode')
            known=type(code) is int and kind!='debug'
            state='success' if known and code==0 else 'error' if known and code not in (130,137,143) else 'paused'
            detail='Concluído' if state=='success' else 'Terminou com erro' if state=='error' else 'Sessão de depuração encerrada' if kind=='debug' else 'Encerrado sem confirmação de sucesso'
            reporter.emit(title,detail,state=state,final=True)
        else:raise ValueError('Operação inválida.')
    def heartbeat(self):
        for reporter,title,kind in self.entries.values():reporter.emit(title,KINDS[kind][1])
    def close(self):
        for reporter,title,_ in self.entries.values():reporter.emit(title,'Editor desconectado; estado final desconhecido',state='paused',final=True)
        self.entries.clear()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--app',choices=['vscode','vscodium'],required=True)
    bridge=Bridge(parser.parse_args().app);pending=b'';next_heartbeat=0
    try:
        while True:
            if select.select([sys.stdin.buffer],[],[],.5)[0]:
                import os
                data=os.read(sys.stdin.fileno(),4096)
                if not data:break
                pending+=data
                if len(pending)>16384:break
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1)
                    try:bridge.receive(json.loads(line))
                    except (ValueError,TypeError):print('Evento de editor recusado.',file=sys.stderr)
            if time.monotonic()>=next_heartbeat:bridge.heartbeat();next_heartbeat=time.monotonic()+3
    finally:bridge.close()
    return 0


if __name__=='__main__':raise SystemExit(main())
