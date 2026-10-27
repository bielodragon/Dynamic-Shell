"""Atividades efêmeras próprias; nunca grava comandos, tokens ou saída bruta."""
import json
import os
from pathlib import Path
import time
import uuid
from theme_store import config,write_json

SOURCES={'steam','localsend','minecraft','terminal','editors'}


def directory():
    runtime=os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:raise RuntimeError('Sessão de usuário indisponível.')
    path=Path(runtime)/'ilha/app-activities';path.mkdir(mode=0o700,parents=True,exist_ok=True)
    return path


class Reporter:
    def __init__(self,source):
        if source not in SOURCES:raise ValueError('Fonte inválida.')
        self.source=source;self.id=source+':session:'+uuid.uuid4().hex
        try:self.path=directory()/(self.id.replace(':','-')+'.json')
        except (OSError,RuntimeError):self.path=None
        self.last=0;self.payload=None
    def emit(self,title,detail='',state='running',progress=None,final=False):
        try:
            if self.path is None:return
            settings=config()
            if settings.get('modules',{}).get('activities') is False or settings.get('integrations',{}).get(self.source) is False:
                self.path.unlink(missing_ok=True);return
            payload={'id':self.id,'app':{'steam':'Steam','localsend':'LocalSend','minecraft':'Minecraft Java','terminal':'Terminal','editors':'Editor'}[self.source],
                'title':str(title)[:120],'detail':str(detail)[:300],'state':state,'progress':progress,'ttl':8 if final else 12}
            now=time.time()
            if payload==self.payload and now-self.last<3:return
            write_json(self.path,{'source':self.source,'pid':os.getpid(),'expires':now+(8 if final else 12),'final':final,'activity':payload})
            self.payload=payload;self.last=now
        except (OSError,ValueError,RuntimeError):pass


def read_events(enabled):
    rows=[];now=time.time()
    for path in sorted(directory().glob('*.json')):
        try:
            if path.stat().st_size>8192:continue
            data=json.loads(path.read_text())
            if data['expires']<now:
                path.unlink();continue
            source=data['source']
            if source not in SOURCES or enabled.get(source) is False:continue
            if not data.get('final'):
                proc=Path('/proc')/str(int(data['pid']))
                if not proc.exists() or proc.stat().st_uid!=os.getuid():continue
            row=data['activity'];row['ttl']=max(1,min(12,data['expires']-now));rows.append(row)
        except (OSError,ValueError,KeyError,TypeError):continue
    return rows[:8]
