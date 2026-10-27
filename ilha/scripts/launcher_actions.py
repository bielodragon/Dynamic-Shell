"""Ações do shell com argumentos separados; pesquisar nunca aplica uma ação."""
import os
from pathlib import Path
import random
import shutil
import subprocess
import wallpaper_store

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff'}


def wallpaper_directory():
    return Path.home() / 'Pictures' / 'Wallpapers'


def wallpapers():
    directory = wallpaper_directory()
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(directory.rglob('*'), key=lambda p: str(p).casefold()):
        if path.suffix.lower() not in IMAGE_EXTENSIONS | wallpaper_store.ANIMATED_EXTENSIONS or not path.is_file():
            continue
        # A seleção só pode apontar para imagens dentro da pasta escolhida.
        if not path.resolve().is_relative_to(directory.resolve()):
            continue
        animated = path.suffix.lower() in wallpaper_store.ANIMATED_EXTENSIONS
        video = animated and path.suffix.lower() != '.gif'
        rows.append({'kind': 'wallpaper', 'id': str(path), 'title': path.stem,
                     'detail': ('Vídeo · ' if video else 'GIF animado · ' if animated else '') + str(path.relative_to(directory)),
                     'thumbnail': wallpaper_store.thumbnail(path) if video else path.as_uri(),
                     'icon': 'video-x-generic' if video else 'preferences-desktop-wallpaper'})
    return rows


def apply_wallpaper(path):
    candidate = Path(path).expanduser().resolve()
    if (not candidate.is_relative_to(wallpaper_directory().resolve())
            or not candidate.is_file() or candidate.suffix.lower() not in IMAGE_EXTENSIONS | wallpaper_store.ANIMATED_EXTENSIONS):
        raise ValueError('Escolha uma imagem de ~/Pictures/Wallpapers.')
    if candidate.suffix.lower() in wallpaper_store.ANIMATED_EXTENSIONS:
        wallpaper_store.select(candidate)
        return
    executable = shutil.which('caelestia')
    if executable: args = [executable, 'wallpaper', '-f', str(candidate), '-N']
    else:
        executable = shutil.which('awww') or shutil.which('swww')
        if not executable: raise RuntimeError('Wallpaper indisponível: use Caelestia ou um daemon awww/swww já iniciado.')
        args = [executable, 'img', str(candidate)]
    result = subprocess.run(args,
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Não foi possível aplicar o wallpaper. Confira se o provedor está iniciado.')
    wallpaper_store.stop_if_active()


def random_wallpaper():
    rows = wallpapers()
    if not rows:
        raise ValueError('Adicione imagens em ~/Pictures/Wallpapers para sortear um wallpaper.')
    state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state'))
    current_file = state / 'caelestia/wallpaper/path.txt'
    current = current_file.read_text().strip() if current_file.is_file() else ''
    from theme_store import config
    animated = config().get('wallpaper',{})
    if animated.get('enabled'): current = animated.get('path',current)
    choices = [row for row in rows if row['id'] != current] or rows
    apply_wallpaper(random.choice(choices)['id'])


def lock():
    # O lock do Caelestia já é o provedor da sessão; não iniciar outro shell.
    executable = shutil.which('caelestia')
    if not executable:
        executable = shutil.which('hyprlock') or shutil.which('swaylock')
        if not executable: raise RuntimeError('Nenhum bloqueador disponível: Caelestia, hyprlock ou swaylock.')
        subprocess.Popen([executable],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return
    result = subprocess.run([executable, 'shell', 'lock', 'lock'],
                            capture_output=True, text=True, timeout=5)
    if result.returncode:
        raise RuntimeError('Não foi possível solicitar o bloqueio da sessão.')
