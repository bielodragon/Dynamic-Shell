"""Arquivos locais para o fundo animado nativo da Ilha."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ANIMATED_EXTENSIONS = {'.gif','.mp4','.webm','.mkv','.mov','.m4v'}


def root():
    return Path.home()/'Pictures/Wallpapers'


def multimedia_available():
    return Path('/usr/lib/qt6/qml/QtMultimedia/qmldir').exists()


def describe(path):
    if not isinstance(path,str) or not path or len(path)>4096 or '\x00' in path:
        raise ValueError('Informe uma imagem animada ou vídeo de ~/Pictures/Wallpapers.')
    candidate=Path(path).expanduser().resolve()
    if not candidate.is_relative_to(root().resolve()) or not candidate.is_file() or candidate.suffix.lower() not in ANIMATED_EXTENSIONS:
        raise ValueError('Escolha GIF, MP4, WebM, MKV, MOV ou M4V dentro de ~/Pictures/Wallpapers.')
    executable=shutil.which('ffprobe')
    if not executable: raise ValueError('Instale ffmpeg para validar wallpapers animados.')
    result=subprocess.run([executable,'-v','error','-protocol_whitelist','file,pipe','-select_streams','v:0',
        '-show_entries','stream=width,height','-of','json',str(candidate)],capture_output=True,text=True,timeout=8)
    streams=json.loads(result.stdout or '{}').get('streams',[])
    if result.returncode or not streams or streams[0].get('width',0)<=0 or streams[0].get('height',0)<=0:
        raise ValueError('O arquivo não contém vídeo ou animação reconhecível.')
    if not multimedia_available():
        raise ValueError('Instale qt6-multimedia e um backend de mídia (no Arch, qt6-multimedia-ffmpeg).')
    return {'path':str(candidate),'kind':'gif' if candidate.suffix.lower()=='.gif' else 'video',**streams[0]}


def thumbnail(path,create=False):
    path=Path(path)
    signature=str(path.resolve())+':'+str(path.stat().st_mtime_ns)+':'+str(path.stat().st_size)
    cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'ilha/wallpapers'
    target=cache/(hashlib.sha256(signature.encode()).hexdigest()+'.jpg')
    if create and not target.exists() and shutil.which('ffmpeg'):
        cache.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix('.tmp.jpg')
        try:
            result=subprocess.run(['ffmpeg','-v','error','-nostdin','-protocol_whitelist','file,pipe','-i',str(path),
                '-frames:v','1','-vf','scale=256:-2','-y',str(temporary)],capture_output=True,timeout=8)
            if not result.returncode: temporary.replace(target)
        except (OSError,subprocess.SubprocessError): pass
        finally: temporary.unlink(missing_ok=True)
    return target.as_uri() if target.exists() else ''


def request(method,*args):
    base=['/usr/bin/quickshell','-c','ilha','ipc','call','wallpaper']
    result=subprocess.run(base+[method,*args],capture_output=True,text=True,timeout=4)
    if result.returncode: raise RuntimeError('Inicie a Ilha para usar o fundo animado.')
    return result.stdout.strip()


def select(path):
    identifier=request('select',str(path))
    if not identifier: raise RuntimeError('O seletor de wallpaper está ocupado. Aguarde e tente novamente.')
    deadline=time.monotonic()+24
    while time.monotonic()<deadline:
        data=json.loads(request('status'))
        if data['requestId']==identifier:
            if data['message']: raise RuntimeError(data['message'])
            if not data['busy'] and data['enabled'] and data['ready']: return
        time.sleep(.1)
    request('stop')
    raise RuntimeError('O wallpaper não ficou pronto. O fundo anterior foi preservado.')


def stop_if_active():
    from theme_store import config
    if not config().get('wallpaper',{}).get('enabled'): return
    request('stop')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if not json.loads(request('status'))['enabled']: return
        time.sleep(.1)
    raise RuntimeError('Não foi possível desativar o fundo animado.')
