#!/usr/bin/env python3
"""Qt Multimedia real em offscreen com vídeos/GIFs próprios e configuração temporária."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-wallpaper-test-') as folder:
        root=Path(folder)
        for name in ('services','components','modules'): (root/name).symlink_to(ROOT/name,target_is_directory=True)
        scripts=root/'scripts';scripts.mkdir()
        for path in (ROOT/'scripts').iterdir():
            if path.is_file(): (scripts/path.name).symlink_to(path)
        (scripts/'device_metrics.py').unlink()
        sensor=root/'battery.json';sensor.write_text(json.dumps({'battery':{'available':False,'batteries':[]}}))
        (scripts/'device_metrics.py').write_text('import json,time\nfrom pathlib import Path\nwhile True:\n try: print(json.dumps(json.loads(Path('+repr(str(sensor))+').read_text())),flush=True)\n except ValueError: pass\n time.sleep(.1)\n')
        walls=root/'Pictures/Wallpapers';walls.mkdir(parents=True)
        for name,options in [('video # teste.mp4',['-c:v','libx264','-pix_fmt','yuv420p']),('animacao.gif',[])]:
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=8','-t','2','-an',*options,'-y',str(walls/name)],check=True,timeout=15)
        (root/'TestSurface.qml').write_text('''import QtQuick
import Quickshell
import qs.modules
import qs.services
FloatingWindow {
    id: testWindow
    implicitWidth:160; implicitHeight:90
    visible:WallpaperState.enabled && content.mediaReady
    WallpaperContent { id:content; anchors.fill:parent }
    Timer { interval:100; repeat:true; running:true; onTriggered:WallpaperState.report(testWindow.screen.name,{ready:content.mediaReady,paused:content.pausePlayback,kind:WallpaperState.gif?"gif":"video",position:content.position,duration:content.duration}) }
    Component.onDestruction: WallpaperState.forget(screen.name)
}''')
        (root/'shell.qml').write_text('''import Quickshell
import qs.services
ShellRoot {
    readonly property bool loaded: WallpaperState.enabled
    Variants {
        model: Quickshell.screens
        delegate: LazyLoader {
            required property var modelData
            source: Quickshell.shellPath("TestSurface.qml")
            activeAsync: WallpaperState.enabled
            onActiveChanged: if (active && item) item.screen=modelData
        }
    }
}''')
        env=dict(os.environ,HOME=str(root),XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_MEDIA_BACKEND='ffmpeg',QT_QPA_PLATFORMTHEME='generic')
        named=root/'config/quickshell';named.mkdir(parents=True)
        (named/'ilha').symlink_to(root,target_is_directory=True)
        with (root/'log').open('w+') as log:
            process=subprocess.Popen(['/usr/bin/quickshell','-c','ilha','--no-color'],env=env,stdout=log,stderr=log)
            def ipc(method,*args):return subprocess.check_output(['/usr/bin/quickshell','ipc','--pid',str(process.pid),'call','wallpaper',method,*args],env=env,text=True,stderr=subprocess.DEVNULL,timeout=4).strip()
            def wait(predicate):
                deadline=time.monotonic()+18
                while time.monotonic()<deadline:
                    try:
                        state=json.loads(ipc('status'))
                        if not state['busy'] and predicate(state):return state
                    except (ValueError,subprocess.SubprocessError):pass
                    time.sleep(.1)
                log.seek(0);raise AssertionError(str(state)+'\n'+log.read())
            def frame(state):return next(iter(state['surfaces'].values()))['position']
            try:
                wait(lambda s:not s['enabled'])
                response=json.loads(subprocess.check_output(['python3',str(ROOT/'scripts/launcher_backend.py'),'wallpaper',json.dumps({'path':str(walls/'video # teste.mp4')})],env=env,text=True,timeout=35))
                assert response['ok'],response
                wait(lambda s:s['ready'] and frame(s)>100)
                ipc('pause','true');wait(lambda s:s['paused'] and all(v['paused'] for v in s['surfaces'].values()))
                time.sleep(1.2);before=frame(json.loads(ipc('status')));time.sleep(1.1)
                assert abs(frame(json.loads(ipc('status')))-before)<80,'O vídeo continuou avançando pausado.'
                ipc('pause','false');wait(lambda s:not s['paused'] and s['ready'] and abs(frame(s)-before)>100)
                sensor.write_text(json.dumps({'battery':{'available':True,'batteries':[{'percent':42,'status':'Discharging'}]}}))
                wait(lambda s:s['paused'] and all(v['paused'] for v in s['surfaces'].values()))
                sensor.write_text(json.dumps({'battery':{'available':True,'batteries':[{'percent':42,'status':'Charging'}]}}))
                wait(lambda s:not s['paused'])
                ipc('select',str(walls/'animacao.gif'))
                state=wait(lambda s:s['ready'] and next(iter(s['surfaces'].values()))['kind']=='gif')
                first=frame(state);wait(lambda s:s['ready'] and frame(s)!=first)
                ipc('stop');wait(lambda s:not s['enabled'] and not s['surfaces'])
                previous=json.loads((root/'config/ilha/config.json').read_text())['wallpaper']
                ipc('select',str(walls/'missing.mp4'));wait(lambda s:bool(s['message']))
                assert json.loads((root/'config/ilha/config.json').read_text())['wallpaper']==previous
                log.seek(0);output=log.read()
                assert 'TypeError' not in output and 'ReferenceError' not in output,output
                print('OK: backend do launcher, MP4 com espaço/#, reprodução/pausa, bateria simulada, GIF, descarregamento e arquivo inválido.')
            finally:process.terminate();process.wait(timeout=5)


if __name__=='__main__':main()
