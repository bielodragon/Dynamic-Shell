#!/usr/bin/env python3
"""LocalSend CLI interativo: a escolha e aceitação continuam com o usuário."""
import shutil
import sys
from activity_process import relay
from app_events import Reporter
from app_streams import LocalSendParser


def main():
    executable=shutil.which('localsend-cli')
    if not executable:print('LocalSend CLI não instalado.',file=sys.stderr);return 1
    reader=LocalSendParser();reporters={key:Reporter('localsend') for key in ('S','R')};active={}
    def output(data):
        for key,payload,final in reader.feed(data):
            reporters[key].emit(**payload,final=final)
            if final:active.pop(key,None)
            else:active[key]=payload
    def heartbeat():
        for key,payload in active.items():reporters[key].emit(**payload)
    try:
        result=relay([executable,*sys.argv[1:]],output,heartbeat,interactive=True)
        for key in active:
            reporters[key].emit('Sessão LocalSend encerrada','Conclusão da transferência não confirmada',state='paused',final=True)
        return result if result>=0 else 128-result
    except (OSError,ValueError) as error:print(str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
