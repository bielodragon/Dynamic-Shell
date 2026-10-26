#!/usr/bin/env python3
"""Preferências em JSON temporário → módulos QML reais, sem mudar as preferências pessoais."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ilha-preferences-test-') as directory:
        folder = Path(directory)
        for name in ('services', 'scripts', 'components'):
            (folder / name).symlink_to(ROOT / name, target_is_directory=True)
        config = folder / 'config'
        config.mkdir()
        env = dict(os.environ, XDG_CONFIG_HOME=str(config), QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='generic')
        (folder / 'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
ShellRoot {
    IpcHandler {
        target: "prefs-test"
        function apply(value: string): void { ThemeStore.setPreferences(JSON.parse(value)); }
        function status(): string {
            return JSON.stringify({ready:ThemeStore.ready, busy:ThemeStore.busy,
                config:ThemeStore.config, duration:Theme.contentDuration,
                islandVisible:ShellState.islandVisible,
                privacy:PrivacyState.enabled, phone:KdeConnectState.enabled,
                privacyObserver:PrivacyState.observerRunning, phoneObserver:KdeConnectState.observerRunning,
                notifications:NotificationState.enabled, activities:ActivityState.enabled,
                mediaVisible:!!MediaState.visiblePlayer, obsEnabled:ObsState.integrationEnabled});
        }
    }
}''')
        with (folder / 'qml.log').open('w+') as log:
            process = subprocess.Popen(['/usr/bin/quickshell', '-p', str(folder), '--no-color'], stdout=log, stderr=log, env=env)
            def ipc(method, *args):
                return subprocess.run(['/usr/bin/quickshell', 'ipc', '--pid', str(process.pid),
                    'call', 'prefs-test', method, *args], capture_output=True, text=True, timeout=3)
            def wait_for(predicate):
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    try:
                        data = json.loads(ipc('status').stdout)
                        if data['ready'] and not data['busy'] and predicate(data): return data
                    except ValueError: pass
                    time.sleep(.1)
                log.seek(0)
                raise AssertionError('Preferências não chegaram aos módulos.\n' + log.read())
            try:
                wait_for(lambda s: s['privacy'] and s['phone'] and s['notifications'] and s['activities'])
                modules = dict.fromkeys(['clock','workspaces','notifications','media','activities','privacy','phone','launcher'], False)
                ipc('apply', json.dumps({'modules':modules, 'animations':{'enabled':False}}))
                wait_for(lambda s: not any([s['privacy'],s['phone'],s['privacyObserver'],s['phoneObserver'],s['notifications'],s['activities'],s['mediaVisible'],s['obsEnabled']]) and s['duration'] == 0)
                saved = json.loads((config / 'ilha/config.json').read_text())
                assert saved['modules'] == modules and not saved['animations']['enabled']
                ipc('apply', json.dumps({'modules':dict.fromkeys(modules, True), 'animations':{'enabled':True,'scale':2}}))
                wait_for(lambda s: s['privacy'] and s['phone'] and s['privacyObserver'] and s['phoneObserver'] and s['notifications'] and s['activities'] and s['duration'] == 360)
                ipc('apply',json.dumps({'shell':{'islandVisible':False},'corners':{'enabled':False,'radius':24},'sync':{'portal':False}}))
                wait_for(lambda s: not s['islandVisible'] and s['config']['corners']['radius']==24)
                ipc('apply',json.dumps({'shell':{'islandVisible':True}}))
                wait_for(lambda s: s['islandVisible'])
                log.seek(0)
                text = log.read()
                assert 'ERROR' not in text and 'TypeError' not in text and 'ReferenceError' not in text, text
                print('OK: persistência temporária, módulos desligam/religam, OBS acompanha privacidade e animações mudam sem reiniciar.')
            finally:
                process.terminate(); process.wait(timeout=5)


if __name__ == '__main__': main()
