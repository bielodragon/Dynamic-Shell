#!/usr/bin/env python3
"""Atualiza a instalação pela release pública, sem modificar checkouts Git."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlparse
from urllib.request import Request,urlopen

REPOSITORY='bielodragon/Dynamic-Shell'
API='https://api.github.com/repos/'+REPOSITORY+'/releases/latest'
SOURCE=Path(__file__).resolve().parents[1]
RECEIPT='.ilha-install.json'


def download(url,limit):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in ('api.github.com','github.com'):raise ValueError('URL de atualização inválida.')
    request=Request(url,headers={'User-Agent':'Dynamic-Shell-Updater','Accept':'application/vnd.github+json' if parsed.hostname=='api.github.com' else 'application/octet-stream'})
    with urlopen(request,timeout=20) as stream:
        final=urlparse(stream.geturl());host=final.hostname or ''
        if final.scheme!='https':raise ValueError('Download exige HTTPS.')
        if host not in ('api.github.com','github.com') and not host.endswith('.githubusercontent.com'):raise ValueError('Redirecionamento inesperado.')
        data=stream.read(limit+1)
    if len(data)>limit:raise ValueError('Arquivo de atualização excede o limite.')
    return data


def latest():
    release=json.loads(download(API,1024*1024))
    if release.get('draft') or release.get('prerelease'):raise ValueError('A release não é estável.')
    tag=release.get('tag_name','')
    if not isinstance(tag,str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',tag):raise ValueError('Tag inválida.')
    assets={row['name']:row for row in release.get('assets',[])}
    candidates=[name for name in assets if re.fullmatch(r'ilha-shell-[a-f0-9]{7,40}\.tar\.gz',name) and name+'.sha256' in assets]
    if len(candidates)!=1:raise ValueError('A release precisa ter um pacote Ilha e seu SHA-256.')
    name=candidates[0]
    for item in (assets[name],assets[name+'.sha256']):
        if not item['browser_download_url'].startswith('https://github.com/'+REPOSITORY+'/releases/download/'):
            raise ValueError('Origem de download inesperada.')
    return {'tag':tag,'name':name,'archive':assets[name]['browser_download_url'],'checksum':assets[name+'.sha256']['browser_download_url']}


def extract_verified(archive,checksum,name,destination):
    lines=checksum.decode('ascii').splitlines()
    expected=next((line.split()[0] for line in lines if len(line.split())==2 and line.split()[1].lstrip('*')==name),'')
    if not re.fullmatch(r'[a-fA-F0-9]{64}',expected) or hashlib.sha256(archive).hexdigest()!=expected.lower():raise ValueError('SHA-256 do pacote não confere.')
    import io
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as package:
        members=package.getmembers()
        if len(members)>5000 or sum(member.size for member in members)>64*1024*1024:raise ValueError('Pacote grande demais.')
        for member in members:
            parts=PurePosixPath(member.name).parts
            if not parts or parts[0]!='ilha-shell' or '..' in parts or not (member.isfile() or member.isdir()):raise ValueError('Caminho/tipo inválido no pacote.')
        package.extractall(destination,filter='data')
    root=Path(destination)/'ilha-shell'
    for relative in ('ilha/shell.qml','ilha/scripts/install_shell.py','install.sh','install-system.sh'):
        if not (root/relative).is_file():raise ValueError('Pacote incompleto.')
    return root


def git_checkout(source):return any((parent/'.git').exists() for parent in (source,*source.parents))


def main(check=False):
    try:
        release=latest();installed={}
        try:installed=json.loads((SOURCE/RECEIPT).read_text())
        except (OSError,ValueError):pass
        print('Release disponível: '+release['tag'])
        print('Versão instalada: '+str(installed.get('release') or 'não identificada'))
        checkout=git_checkout(SOURCE)
        if checkout:print('Esta instalação é um checkout Git; a atualização automática está desativada para preservar o desenvolvimento.')
        if check:return 0
        if os.geteuid()==0:raise ValueError('Execute ilha update como usuário, sem sudo.')
        if checkout:raise ValueError('Atualize o checkout pelo seu fluxo Git. ilha update funciona na cópia instalada por install.sh/install-system.sh.')
        if installed.get('release')==release['tag']:print('A Ilha já está atualizada.');return 0
        system=SOURCE==Path('/etc/xdg/quickshell/ilha')
        expected=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'quickshell/ilha'
        if not system and SOURCE!=expected.resolve():raise ValueError('Execute o comando ilha da instalação pessoal ou global.')
        if not sys.stdin.isatty():raise ValueError('Abra um terminal para confirmar, ou use ilha update --check.')
        if input('Baixar, verificar e instalar '+release['tag']+' com backup? [s/N] ').strip().lower() not in ('s','sim'):print('Cancelado.');return 0
        with tempfile.TemporaryDirectory(prefix='ilha-update-') as temp:
            root=extract_verified(download(release['archive'],16*1024*1024),download(release['checksum'],16384),release['name'],temp)
            (root/'ilha'/RECEIPT).write_text(json.dumps({'repository':REPOSITORY,'release':release['tag'],'scope':'system' if system else 'user'}))
            # Só o instalador do sistema eleva privilégios; configuração pessoal não muda.
            args=(['sudo'] if system else [])+[sys.executable,str(root/'ilha/scripts/install_shell.py'),'--system' if system else '--user','--non-interactive']
            subprocess.run(args,check=True)
        print('Atualização instalada. Backups do código e comandos foram mantidos pelo instalador.')
        from desktop_cli import running
        if running():
            subprocess.run([sys.executable,str(SOURCE/'scripts/desktop_cli.py'),'reload'],check=True)
        return 0
    except Exception as error:
        print('Atualização: '+str(error),file=sys.stderr)
        print('Se o instalador ou reload falhou, preserve os backups .bak.ilha-* ao lado da instalação para restauração.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main('--check' in sys.argv))
