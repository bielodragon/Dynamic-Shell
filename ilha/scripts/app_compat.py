#!/usr/bin/env python3
"""Ajustes opt-in deste usuário para Electron/Chromium; não altera drivers."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def apply():
    home = Path.home()
    config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state')) / 'ilha'
    state.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    manifest = []

    def write(path, text):
        if path.exists() and path.read_text() == text: return
        previous = None
        if path.exists():
            previous = str(path) + '.bak.ilha-compat-' + stamp
            shutil.copy2(path, previous)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink(): path.unlink()
        path.write_text(text)
        manifest.append({'path': str(path), 'backup': previous})

    def json_settings(path, update):
        # Não destruir JSONC ou formatos que não sabemos preservar.
        data = json.loads(path.read_text()) if path.exists() else {}
        for key, value in update.items(): data[key] = value
        write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    running = subprocess.run(['pgrep','-u',str(os.getuid()),'-x','chrome|chromium|codium|Discord|firefox'],capture_output=True)
    if running.returncode == 0:
        raise RuntimeError('Feche Chrome, Chromium, VSCodium, Discord e Firefox antes de aplicar, para preservar seus perfis.')
    for name in ('chrome','chromium'):
        path = config / (name + '-flags.conf')
        flags = path.read_text() if path.exists() else ''
        if '--disable-gpu' not in flags.splitlines(): write(path, flags.rstrip() + '\n--disable-gpu\n')
    json_settings(config / 'VSCodium/argv.json', {'disable-hardware-acceleration': True})
    json_settings(config / 'VSCodium/User/settings.json', {'window.titleBarStyle': 'native'})
    # Override pessoal do launcher; não modificar /usr/share/applications.
    for filename in ('discord.desktop','vscodium.desktop','vscodium-wayland.desktop','vscodium-uri-handler.desktop'):
        source = Path('/usr/share/applications') / filename
        if not source.exists(): continue
        target = home / '.local/share/applications' / filename
        original = target.read_text() if target.exists() else source.read_text()
        lines = []
        for line in original.splitlines():
            if line.startswith('Exec=') and '--disable-gpu' not in line:
                executable, separator, arguments = line.partition(' ')
                line = executable + ' --disable-gpu' + (' ' + arguments if separator else '')
            lines.append(line)
        write(target, '\n'.join(lines) + '\n')
    for browser in ('google-chrome','chromium'):
        for path in (config / browser).glob('*/Preferences'):
            data = json.loads(path.read_text())
            data.setdefault('browser', {})['custom_chrome_frame'] = False
            write(path, json.dumps(data, ensure_ascii=False, separators=(',',':')))
    for base in (home / '.mozilla/firefox', config / 'mozilla/firefox'):
        for prefs in base.glob('*/prefs.js'):
            target = prefs.parent / 'user.js'
            text = target.read_text() if target.exists() else ''
            text = re.sub(r'^\s*user_pref\("browser\.tabs\.inTitlebar",[^\n]*\);\s*$', '', text, flags=re.M)
            write(target, text.rstrip() + '\nuser_pref("browser.tabs.inTitlebar", 0);\n')
    record = state / ('app-compat-' + stamp + '.json')
    record.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'changed': [row['path'] for row in manifest], 'backups': str(record)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', required=True)
    parser.parse_args()
    apply()
