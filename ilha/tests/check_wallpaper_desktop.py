#!/usr/bin/env python3
"""Opt-in: wallpaper de teste temporário, restauração do workspace e das opções."""
import json
from pathlib import Path
import subprocess
import time
import uuid
from urllib.parse import unquote, urlparse
from check_launcher_desktop import require_unlocked

BASE=['/usr/bin/quickshell','-c','ilha','ipc','call']


def ipc(target,method,*args):return subprocess.check_output(BASE+[target,method,*args],text=True,timeout=5).strip()
def state():return json.loads(ipc('wallpaper','status'))
def wait(predicate):
    deadline=time.monotonic()+18
    while time.monotonic()<deadline:
        data=state()
        if not data['busy'] and predicate(data):return data
        time.sleep(.15)
    raise RuntimeError('Wallpaper não chegou ao estado esperado: '+str(state()))
def focus(name):subprocess.run(['hyprctl','eval','hl.dispatch(hl.dsp.focus({workspace='+json.dumps(name)+'}))'],check=True,capture_output=True)
def position(data):return next(iter(data['surfaces'].values()))['position']


def main():
    require_unlocked()
    previous=state();device=json.loads(ipc('device','status'))
    workspace=json.loads(subprocess.check_output(['hyprctl','-j','activeworkspace'],text=True))
    workspaces=json.loads(subprocess.check_output(['hyprctl','-j','workspaces'],text=True))
    target=str(max([row['id'] for row in workspaces if row['id']>0]+[1])+1)
    token=uuid.uuid4().hex[:10];walls=Path.home()/'Pictures/Wallpapers'
    media=[walls/('_ilha-teste-'+token+'.mp4'),walls/('_ilha-teste-'+token+'.gif')]
    terminal=None
    try:
        for path in media:
            extra=['-c:v','libx264','-pix_fmt','yuv420p'] if path.suffix=='.mp4' else []
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=8','-t','3','-an',*extra,'-y',str(path)],check=True,timeout=15)
        focus(target)
        response=json.loads(subprocess.check_output(['python3','ilha/scripts/launcher_backend.py','wallpaper',json.dumps({'path':str(media[0])})],text=True,timeout=35))
        assert response['ok'],response
        wait(lambda s:s['ready'] and position(s)>100)
        time.sleep(.5);subprocess.run(['timeout','8s','grim','/tmp/ilha-wallpaper-video.png'],check=True)
        ipc('wallpaper','pause','true');wait(lambda s:s['paused'] and all(v['paused'] for v in s['surfaces'].values()))
        time.sleep(1.1);before=position(state());time.sleep(1.1)
        assert abs(position(state())-before)<100
        ipc('wallpaper','pause','false');wait(lambda s:not s['paused'] and abs(position(s)-before)>100)
        ipc('device','setPerformance','true')
        wait(lambda s:s['paused'])
        ipc('device','setPerformance','false');wait(lambda s:not s['paused'])
        with open('/tmp/ilha-wallpaper-terminal.log','w') as log:
            terminal=subprocess.Popen(['foot','--app-id','ilha-wallpaper-test','sleep','30'],stdout=log,stderr=log)
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                active=json.loads(subprocess.check_output(['hyprctl','-j','activewindow'],text=True))
                if active.get('class')=='ilha-wallpaper-test':break
                time.sleep(.1)
            assert active.get('class')=='ilha-wallpaper-test'
            subprocess.run(['hyprctl','eval','hl.dispatch(hl.dsp.window.fullscreen({mode="fullscreen"}))'],check=True,capture_output=True)
            wait(lambda s:s['ready'] and all(v['paused'] for v in s['surfaces'].values()))
            terminal.terminate();terminal.wait(timeout=5);terminal=None
        wait(lambda s:s['ready'] and not any(v['paused'] for v in s['surfaces'].values()))
        ipc('wallpaper','select',str(media[1]));first=wait(lambda s:s['ready'] and next(iter(s['surfaces'].values()))['kind']=='gif')
        wait(lambda s:s['ready'] and position(s)!=position(first))
        subprocess.run(['timeout','8s','grim','/tmp/ilha-wallpaper-gif.png'],check=True)
        ipc('settings','open','wallpaper');time.sleep(.7)
        subprocess.run(['timeout','8s','grim','/tmp/ilha-wallpaper-configuracoes.png'],check=True)
        print('OK: backend do launcher, vídeo/GIF reais, pausa manual, desempenho, tela cheia e capturas.')
    finally:
        if terminal and terminal.poll() is None:terminal.terminate();terminal.wait(timeout=5)
        ipc('settings','close')
        ipc('device','setPerformance','true' if device['controls'].get('performance') else 'false')
        ipc('wallpaper','configure',json.dumps(previous['options']))
        wait(lambda s:s['enabled']==previous['enabled'] and s['path']==previous['path'])
        focus(str(workspace['name']))
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        from wallpaper_store import thumbnail
        for path in media:
            if path.exists():
                preview=thumbnail(path)
                if preview:Path(unquote(urlparse(preview).path)).unlink(missing_ok=True)
            path.unlink(missing_ok=True)


if __name__=='__main__':main()
