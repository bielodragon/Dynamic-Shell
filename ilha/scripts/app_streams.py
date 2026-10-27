"""Leitura de estados conhecidos; saída privada não é copiada para as atividades."""
import codecs
import re

ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)')
STATUS=re.compile(r'^\s*([SR])\s+.+?\[[#\- ]+\]\s+(\d+(?:\.\d+)?)\s+(B|KB|MB|GB|TB)\s*/\s*(\d+(?:\.\d+)?)\s+(B|KB|MB|GB|TB)\s+\[[^\]]*\]\s+\[ETA:[^\]]*\]')


class LocalSendParser:
    def __init__(self):self.buffer='';self.decoder=codecs.getincrementaldecoder('utf-8')('replace')
    def line(self,line):
        rows=[]
        for part in line.split('  |  '):
            match=STATUS.match(part)
            if match:
                direction=match[1];units={'B':1,'KB':1000,'MB':1000000,'GB':1000000000,'TB':1000000000000}
                done=float(match[2])*units[match[3]];total=float(match[4])*units[match[5]]
                rows.append((direction,{'title':'Enviando arquivos' if direction=='S' else 'Recebendo arquivos',
                    'detail':'Progresso aproximado dos bytes mostrados pelo CLI','state':'running',
                    'progress':round(max(0,min(100,100*done/total)),1) if total>0 else None},False))
            elif re.match(r'^\s*[SR] .+: (?:Sent|Received) \d+ files? \(',part):
                direction=part.strip()[0];failed=bool(re.search(r'\d+ failed',part))
                rows.append((direction,{'title':'Transferência com falhas' if failed else 'Transferência concluída',
                    'detail':'LocalSend CLI','state':'error' if failed else 'success','progress':None if failed else 100},True))
            elif re.match(r'^\s*[SR] .+: ',part) and re.search(r'\b(?:Failed|Declined|Cancelled|cancelled|Blocked)\b',part):
                cancelled=bool(re.search(r'\b(?:Declined|Cancelled|cancelled)\b',part))
                rows.append((part.strip()[0],{'title':'Transferência cancelada' if cancelled else 'Falha na transferência',
                    'detail':'Consulte o terminal do LocalSend','state':'paused' if cancelled else 'error','progress':None},True))
        return rows
    def feed(self,data):
        self.buffer+=self.decoder.decode(data)
        self.buffer=re.sub(r'\x1b\[\d*G','\n',self.buffer)
        self.buffer=ANSI.sub('',self.buffer)[-16384:]
        parts=re.split(r'[\r\n]',self.buffer);self.buffer=parts.pop()
        result=[]
        for part in parts:result+=self.line(part)
        if STATUS.match(self.buffer):result+=self.line(self.buffer);self.buffer=''
        return result


class MinecraftParser:
    def __init__(self):self.buffer='';self.decoder=codecs.getincrementaldecoder('utf-8')('replace')
    def feed(self,data):
        self.buffer+=self.decoder.decode(data);lines=self.buffer.split('\n');self.buffer=lines.pop()[-8192:]
        state=None
        for line in lines:
            if 'Reloading ResourceManager' in line:state='Carregando recursos'
            elif 'Sound engine started' in line:state='Cliente inicializado'
            elif 'Connecting to ' in line:state='Conectando ao servidor'
            elif 'Starting integrated minecraft server' in line:state='Iniciando mundo local'
            elif 'Stopping!' in line:state='Encerrando'
        return state
