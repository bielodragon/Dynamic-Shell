"""Catálogos locais, sem contas, credenciais ou chamadas à rede."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re


def vdf(text):
    if len(text)>8*1024*1024: raise ValueError('Metadados grandes demais.')
    tokens=re.findall(r'//[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}"]+',text)
    tokens=[t for t in tokens if not t.startswith('//')];index=0
    def value(token):
        if token.startswith('"'):
            try:return json.loads(token)
            except ValueError:return token[1:-1].replace('\\\\','\\').replace('\\"','"')
        return token
    def group(depth=0):
        nonlocal index
        if depth>32:raise ValueError('Estrutura VDF inválida.')
        result={}
        while index<len(tokens):
            key=tokens[index];index+=1
            if key=='}':
                if depth==0:raise ValueError('Fechamento VDF inesperado.')
                return result
            if index>=len(tokens):raise ValueError('VDF incompleto.')
            item=tokens[index];index+=1
            result[value(key)]=group(depth+1) if item=='{' else value(item)
        if depth:raise ValueError('VDF incompleto.')
        return result
    return group()


def steam_roots():
    home=Path.home();data=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))
    paths=[data/'Steam',home/'.steam/steam',home/'.steam/root',home/'.steam/debian-installation',
        home/'.var/app/com.valvesoftware.Steam/data/Steam',home/'.var/app/com.valvesoftware.Steam/.local/share/Steam']
    if os.environ.get('ILHA_STEAM_ROOT'):paths.insert(0,Path(os.environ['ILHA_STEAM_ROOT']).expanduser())
    return list(dict.fromkeys(p.resolve() for p in paths if p.is_dir()))


def steam_games():
    libraries=set(steam_roots())
    for root in list(libraries):
        try:
            entries=vdf((root/'steamapps/libraryfolders.vdf').read_text()).get('libraryfolders',{})
            for key,value in entries.items():
                path=value.get('path') if isinstance(value,dict) else value if key.isdigit() else None
                if path and Path(path).is_dir():libraries.add(Path(path).resolve())
        except (OSError,ValueError,AttributeError):pass
    games={}
    for root in sorted(libraries):
        for path in sorted((root/'steamapps').glob('appmanifest_*.acf'))[:3000]:
            try:
                entry=vdf(path.read_text()).get('AppState',{})
                appid=str(entry.get('appid',''))
                if not re.fullmatch(r'[1-9]\d{0,9}',appid) or path.stem!='appmanifest_'+appid:continue
                name=str(entry.get('name','Steam '+appid))[:120]
                total=int(entry.get('BytesToDownload',0));done=int(entry.get('BytesDownloaded',0))
                games[appid]={'id':appid,'name':name,'downloaded':max(0,done),'total':max(0,total)}
            except (OSError,ValueError,AttributeError,TypeError):continue
    return sorted(games.values(),key=lambda game:game['name'].casefold())


def prism_roots():
    data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
    paths=[data/'PrismLauncher']
    if os.environ.get('ILHA_PRISM_ROOT'):paths.insert(0,Path(os.environ['ILHA_PRISM_ROOT']).expanduser())
    return list(dict.fromkeys(p.resolve() for p in paths if p.is_dir()))


def instances():
    result=[]
    for root in prism_roots():
        for path in sorted((root/'instances').glob('*/instance.cfg')):
            try:
                config=configparser.ConfigParser(interpolation=None,strict=False);config.read(path)
                section=config['General']
                identifier=hashlib.sha256(str(path.parent.resolve()).encode()).hexdigest()[:24]
                result.append({'id':identifier,'name':section.get('name',path.parent.name)[:120],
                    'folder':path.parent.name,'root':str(root),'config':str(path)})
            except (OSError,KeyError,ValueError,configparser.Error):continue
    return result


class DownloadTracker:
    def __init__(self):self.previous={};self.active={}
    def sample(self,games,running,now):
        rows=[]
        for game in games:
            key=game['id'];done=game['downloaded'];total=game['total'];old=self.previous.get(key)
            if running and old is not None and done>old and total>0:self.active[key]=now
            if running and key in self.active and now-self.active[key]<15 and total>0 and 0<=done<=total:
                complete=done==total
                rows.append({'id':'steam:download:'+key,'app':'Steam','title':game['name'],
                    'detail':'Transferência concluída' if complete else 'Baixando' if old is not None and done>old else 'Aguardando atualização dos contadores',
                    'state':'success' if complete else 'running','progress':round(done*100/total,1),'ttl':8 if complete else 12})
                if complete:self.active.pop(key,None)
            self.previous[key]=done
        if not running:self.active.clear()
        return rows
