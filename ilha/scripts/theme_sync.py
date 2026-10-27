#!/usr/bin/env python3
"""Sincronização opt-in. Prévia do editor não altera outros aplicativos."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from theme_store import validate_theme, write_json


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=8)
    if result.returncode: raise RuntimeError('Falha em ' + args[0] + ': ' + result.stderr.strip()[:160])


def dark(colors):
    value = colors['background'].lstrip('#')
    values = [int(value[i:i+2], 16) / 255 for i in (0,2,4)]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(linear,(.2126,.7152,.0722))) < .5


def kitty(colors):
    directory = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    target = directory / 'ilha/kitty-colors.conf'; target.parent.mkdir(parents=True, exist_ok=True)
    palette = [colors[key] for key in ('background','error','success','warning','accent','accent','accent','text')]
    content = '\n'.join([f'background {colors["background"]}', f'foreground {colors["text"]}',
                         f'cursor {colors["accent"]}', f'selection_background {colors["accent"]}',
                         f'selection_foreground {colors["background"]}'] +
                        [f'color{i} {color}' for i,color in enumerate(palette + palette)]) + '\n'
    target.write_text(content)
    config = directory / 'kitty/kitty.conf'; config.parent.mkdir(parents=True, exist_ok=True)
    text = config.read_text() if config.exists() else ''
    include = 'include ' + str(target)
    if include not in text.splitlines():
        if config.exists(): shutil.copy2(config, str(config) + '.bak.ilha-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        # Não escrever no destino de links para configurações distribuídas.
        if config.is_symlink(): config.unlink()
        config.write_text(text.rstrip() + '\n\n# Cores gerenciadas pela Ilha (opt-in).\n' + include + '\n')


def synchronize(payload):
    original = payload['theme']; theme = validate_theme(original)
    config = payload.get('config', {}); options = config.get('sync', {})
    colors = theme['colors'].copy()
    accent = config.get('overrides', {}).get('accent')
    if accent:
        import re
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', accent): raise ValueError('Destaque inválido.')
        colors['accent'] = accent
    applied, errors = [], []
    for name in ('portal','kitty','hyprland','wallpaper'):
        if options.get(name) is not True: continue
        try:
            if name == 'portal': run(['gsettings','set','org.gnome.desktop.interface','color-scheme','prefer-dark' if dark(colors) else 'prefer-light'])
            elif name == 'kitty': kitty(colors)
            elif name == 'hyprland':
                for key, color in [('active_border',colors['accent']),('inactive_border',colors['border'])]:
                    run(['hyprctl','keyword','general:col.' + key,'rgba(' + color[1:] + 'ff)'])
            else:
                path = config.get('wallpapers', {}).get(original['id'])
                if not path: continue
                from launcher_actions import apply_wallpaper
                # Evita reaplicar o mesmo arquivo a cada ajuste de preferência.
                state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'ilha/wallpaper.json'
                previous = json.loads(state.read_text()) if state.exists() else {}
                from wallpaper_store import ANIMATED_EXTENSIONS
                animated = Path(path).suffix.lower() in ANIMATED_EXTENSIONS
                active = config.get('wallpaper',{})
                if previous.get('path') == path:
                    if not animated and not active.get('enabled'): continue
                    if animated and active.get('enabled') and Path(active.get('path','')).resolve() == Path(path).expanduser().resolve(): continue
                apply_wallpaper(path); write_json(state, {'path':path})
            applied.append(name)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            errors.append(name + ': ' + str(error))
    return {'ok':not errors,'applied':applied,'errors':errors}


if __name__ == '__main__':
    try: result = synchronize(json.loads(sys.argv[1]))
    except Exception as error: result = {'ok':False,'errors':[str(error)]}
    print(json.dumps(result,ensure_ascii=False))
