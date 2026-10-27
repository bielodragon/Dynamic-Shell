#!/usr/bin/env python3
"""Distribuição reproduzível a partir do HEAD limpo, sem arquivos locais pessoais."""
import argparse
import gzip
import hashlib
from pathlib import Path
import subprocess
import sys


def build(root,output=None):
    root=Path(root).resolve()
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
    if git('status','--porcelain').strip():raise ValueError('Salve/commite as alterações antes de gerar o pacote do HEAD.')
    commit=git('rev-parse','--verify','HEAD^{commit}').decode().strip()
    destination=Path(output) if output else root/'dist'
    destination.mkdir(parents=True,exist_ok=True)
    archive=destination/('ilha-shell-'+commit[:7]+'.tar.gz')
    source=git('archive','--format=tar','--prefix=ilha-shell/',commit)
    with archive.open('wb') as stream:
        with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as compressed:compressed.write(source)
    checksum=archive.with_suffix(archive.suffix+'.sha256')
    checksum.write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    return archive,checksum,commit


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    try:
        root=subprocess.check_output(['git','-C',str(Path(__file__).resolve().parents[2]),'rev-parse','--show-toplevel'],text=True).strip()
        archive,checksum,commit=build(root,args.output)
        print('Commit: '+commit+'\nPacote: '+str(archive)+'\nSHA-256: '+str(checksum));return 0
    except (OSError,ValueError,subprocess.SubprocessError) as error:print(str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
