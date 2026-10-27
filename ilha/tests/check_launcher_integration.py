#!/usr/bin/env python3
"""Launcher QML real com app, terminal e clipboard de teste, sem histórico pessoal."""
import json
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-launcher-test-') as directory:
        folder = Path(directory)
        for name in ('services', 'scripts', 'components'):
            (folder / name).symlink_to(ROOT / name, target_is_directory=True)
        binary = folder / 'bin'; binary.mkdir()
        data = folder / 'data/applications'; data.mkdir(parents=True)
        fixture = folder / 'fixture.py'; launched = folder / 'launched'
        fixture.write_text('from pathlib import Path\nPath(' + repr(str(launched)) + ').write_text("ok")\n')
        (data / 'ilha-launcher-fixture.desktop').write_text('[Desktop Entry]\nType=Application\nName=Ilha Launcher Fixture\nExec=' + sys.executable + ' ' + str(fixture) + '\nIcon=utilities-terminal\n')
        copied, terminal = folder / 'copied', folder / 'terminal.json'
        action_log = folder / 'actions.json'
        steam=folder/'data/Steam/steamapps';steam.mkdir(parents=True)
        (steam/'appmanifest_42.acf').write_text('"AppState" { "appid" "42" "name" "Ilha Jogo Fixture" }')
        prism=folder/'data/PrismLauncher/instances/Ilha mundo';prism.mkdir(parents=True)
        (prism/'instance.cfg').write_text('[General]\nname=Ilha Mundo Fixture\n')
        walls = folder / 'Pictures/Wallpapers'; walls.mkdir(parents=True)
        (walls / 'Ilha teste.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a2ioAAAAASUVORK5CYII='))
        for name, script in {
            'wl-copy':'import sys\nfrom pathlib import Path\nPath(' + repr(str(copied)) + ').write_bytes(sys.stdin.buffer.read())\n',
            'xdg-terminal-exec':'import sys,json\nfrom pathlib import Path\nPath(' + repr(str(terminal)) + ').write_text(json.dumps(sys.argv[1:]))\n',
            'caelestia':'import sys,json\nfrom pathlib import Path\nPath(' + repr(str(action_log)) + ').write_text(json.dumps(sys.argv[1:]))\n'
        }.items():
            path = binary / name; path.write_text('#!' + sys.executable + '\n' + script); path.chmod(0o700)
        env = dict(os.environ, HOME=str(folder), PATH=str(binary) + ':' + os.environ['PATH'], XDG_CONFIG_HOME=str(folder / 'config'),
            XDG_DATA_HOME=str(folder / 'data'), XDG_CACHE_HOME=str(folder / 'cache'),
            ILHA_CLIPHIST_DB=str(folder / 'history.db'), QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='generic')
        content = b'Ilha clipboard <literal>\n'
        subprocess.run(['cliphist','-db-path',env['ILHA_CLIPHIST_DB'],'store'],input=content,env=env,check=True,capture_output=True)
        (folder / 'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
ShellRoot {
    IpcHandler {
        target: "launcher-test"
        function disable(): void { ThemeStore.setPreferences({modules:{launcher:false}}); }
    }
    readonly property bool loadLauncher: LauncherState.enabled
}''')
        with (folder / 'qml.log').open('w+') as log:
            process = subprocess.Popen(['/usr/bin/quickshell','-p',str(folder),'--no-color'],env=env,stdout=log,stderr=log)
            def ipc(method, *args, target='launcher'):
                return subprocess.run(['/usr/bin/quickshell','ipc','--pid',str(process.pid),'call',target,method,*args],capture_output=True,text=True,timeout=3)
            def wait_for(predicate):
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    try:
                        state = json.loads(ipc('status').stdout)
                        if predicate(state): return state
                    except ValueError: pass
                    time.sleep(.1)
                log.seek(0)
                raise AssertionError('Estado esperado não chegou. ' + ipc('status').stdout + '\n' + log.read())
            try:
                wait_for(lambda s: not s['opened'])
                ipc('open',''); ipc('search','Ilha Launcher Fixture')
                wait_for(lambda s: s['resultCount'] == 1)
                assert not launched.exists(), 'Pesquisar não pode executar apps.'
                ipc('activate')
                wait_for(lambda s: not s['opened'])
                deadline = time.monotonic() + 4
                while not launched.exists() and time.monotonic() < deadline: time.sleep(.1)
                assert launched.read_text() == 'ok'
                ipc('open',''); ipc('search','= sqrt(144)+2**3')
                wait_for(lambda s: s['calculatorResult'] == '20')
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert copied.read_bytes() == b'20'
                ipc('open',''); ipc('search',': Ilha clipboard')
                wait_for(lambda s: s['mode']=='clipboard' and s['resultCount']==1 and not s['busy'])
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert copied.read_bytes() == content, 'Clipboard precisa preservar bytes e nova linha.'
                ipc('open',''); ipc('search','> printf "%s" "$(literal)"')
                wait_for(lambda s: s['mode']=='commands' and s['resultCount']==1)
                assert not terminal.exists(), 'Pesquisar não pode executar comandos.'
                ipc('activate'); wait_for(lambda s: not s['opened'])
                args = json.loads(terminal.read_text())
                assert args == ['sh','-lc','printf "%s" "$(literal)"']
                ipc('open',''); ipc('search','>')
                wait_for(lambda s: s['mode']=='commands' and s['resultCount']==9)
                assert not action_log.exists(), 'Mostrar ações não pode mudar wallpaper ou bloquear.'
                ipc('activate')  # Primeira ação: abrir seletor, sem aplicar wallpaper.
                wait_for(lambda s: s['resultCount']==1 and not s['busy'])
                assert not action_log.exists()
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert json.loads(action_log.read_text()) == ['wallpaper','-f',str(walls / 'Ilha teste.png'),'-N']
                ipc('open',''); ipc('search','> random')
                wait_for(lambda s: s['resultCount']==1)
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert json.loads(action_log.read_text())[0] == 'wallpaper'
                ipc('open',''); ipc('search','> lock')
                wait_for(lambda s: s['resultCount']==1)
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert json.loads(action_log.read_text()) == ['shell','lock','lock']
                ipc('open',''); ipc('search','> scheme ')
                wait_for(lambda s: s['resultCount']>=10)
                ipc('search','> scheme Nord'); wait_for(lambda s: s['resultCount']==1)
                ipc('activate'); wait_for(lambda s: not s['opened'])
                assert json.loads((folder / 'config/ilha/config.json').read_text())['theme']=='nord'
                # Catálogos reais, sem iniciar clientes ou jogos.
                saved_terminal=terminal.read_bytes();saved_action=action_log.read_bytes()
                ipc('open','')
                for source,query,count in [('steam','Ilha Jogo Fixture',1),('minecraft','Ilha Mundo Fixture',1),('localsend','LocalSend',2)]:
                    ipc('search','>');wait_for(lambda s:s['resultCount']==9)
                    ipc('search','> '+source+' '+query)
                    wait_for(lambda s:s['resultCount']==count and not s['busy'])
                assert terminal.read_bytes()==saved_terminal and action_log.read_bytes()==saved_action
                for mode, identifier in [('light','light'),('dark','dark')]:
                    ipc('open',''); ipc('search','> '+mode)
                    wait_for(lambda s: s['resultCount']==1)
                    ipc('activate'); wait_for(lambda s: not s['opened'])
                    assert json.loads((folder / 'config/ilha/config.json').read_text())['theme']==identifier
                ipc('disable',target='launcher-test'); time.sleep(.5)
                ipc('open',''); assert not json.loads(ipc('status').stdout)['opened']
                log.seek(0); output=log.read()
                assert 'ERROR' not in output and 'TypeError' not in output, output
                print('OK: app, calculadora, clipboard privado, terminal, catálogo de ações, seletor de wallpaper, sorteio, lock simulado, esquemas, claro/escuro e módulo desativado.')
            finally:
                process.terminate(); process.wait(timeout=5)


if __name__ == '__main__': main()
