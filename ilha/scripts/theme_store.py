#!/usr/bin/env python3
"""Persistência de temas da ilha; usa apenas a biblioteca padrão do Python."""

import json
import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILTINS = ROOT / "themes"
USER_ROOT = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ilha"
USER_THEMES = USER_ROOT / "themes"
CONFIG = USER_ROOT / "config.json"
DEFAULT_CONFIG = ROOT / "config.json"
TOKENS = (
    "background", "surface", "elevatedSurface", "text", "secondaryText",
    "accent", "border", "success", "error", "warning",
)
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MODULES = ('clock', 'workspaces', 'notifications', 'media', 'activities', 'privacy', 'phone', 'launcher')


def read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ilha-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_theme(theme):
    if not isinstance(theme, dict):
        raise ValueError("O tema precisa ser um objeto JSON.")
    name = theme.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 60:
        raise ValueError("Informe um nome de tema com até 60 caracteres.")
    colors = theme.get("colors")
    if not isinstance(colors, dict) or any(not HEX.fullmatch(str(colors.get(token, ""))) for token in TOKENS):
        raise ValueError("O tema precisa conter os dez tokens de cor em #RRGGBB.")
    for setting in ("glassOpacity", "blurIntensity"):
        value = theme.get(setting)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError(f"{setting} precisa estar entre 0 e 1.")
    return {
        "name": name.strip(),
        "colors": {token: colors[token].lower() for token in TOKENS},
        "glassOpacity": float(theme["glassOpacity"]),
        "blurIntensity": float(theme["blurIntensity"]),
    }


def themes():
    result = []
    for directory, builtin in ((BUILTINS, True), (USER_THEMES, False)):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            data = validate_theme(read_json(path))
            data["id"] = path.stem
            data["builtin"] = builtin
            result.append(data)
    return result


def config():
    data = read_json(DEFAULT_CONFIG)
    if CONFIG.exists():
        data.update(read_json(CONFIG))
    data.setdefault("overrides", {"accent": None, "glassOpacity": None, "blurIntensity": None})
    data['modules'] = {**dict.fromkeys(MODULES, True), **(data.get('modules') or {})}
    data['animations'] = {'enabled': True, 'scale': 1.0, **(data.get('animations') or {})}
    return data


def snapshot():
    entries = themes()
    current = config()
    if not any(item["id"] == current.get("theme") for item in entries):
        current["theme"] = "dark"
    return {"themes": entries, "config": current}


def require_theme(theme_id):
    for item in themes():
        if item["id"] == theme_id:
            return item
    raise ValueError("Tema não encontrado.")


def custom_path(theme_id):
    if not re.fullmatch(r"[a-f0-9]{32}", theme_id or ""):
        raise ValueError("Identificador de tema inválido.")
    return USER_THEMES / f"{theme_id}.json"


def update_config(changes):
    current = config()
    current.update(changes)
    write_json(CONFIG, current)


def perform(operation, payload):
    if operation == "snapshot":
        return snapshot()
    if operation == "select":
        theme_id = str(payload.get("id", ""))
        require_theme(theme_id)
        update_config({"theme": theme_id})
    elif operation in ("save", "duplicate", "import"):
        if operation == "import":
            source = Path(str(payload.get("path", ""))).expanduser()
            if not source.is_file() or source.stat().st_size > 65536:
                raise ValueError("Arquivo de tema ausente ou maior que 64 KiB.")
            data = validate_theme(read_json(source))
        elif operation == "duplicate":
            original = require_theme(str(payload.get("id", "")))
            data = validate_theme(original)
            data["name"] = f"{data['name']} — cópia"[:60]
        else:
            data = validate_theme(payload.get("theme"))
        theme_id = str(payload.get("id", "")) if operation == "save" else ""
        if theme_id:
            path = custom_path(theme_id)
            if not path.is_file():
                raise ValueError("Temas prontos não podem ser sobrescritos.")
        else:
            theme_id = uuid.uuid4().hex
            path = custom_path(theme_id)
        data["id"] = theme_id
        write_json(path, data)
        update_config({"theme": theme_id})
    elif operation == "delete":
        theme_id = str(payload.get("id", ""))
        path = custom_path(theme_id)
        if not path.is_file():
            raise ValueError("Só temas pessoais podem ser apagados.")
        path.unlink()
        if config().get("theme") == theme_id:
            update_config({"theme": "dark"})
    elif operation == "export":
        item = require_theme(str(payload.get("id", "")))
        target = Path(str(payload.get("path", ""))).expanduser()
        if not target.is_absolute() or target.exists() or not target.parent.is_dir():
            raise ValueError("Informe um caminho absoluto novo em uma pasta existente.")
        content = {key: item[key] for key in ("name", "colors", "glassOpacity", "blurIntensity")}
        with target.open("x", encoding="utf-8") as stream:
            json.dump(content, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    elif operation == "overrides":
        values = payload.get("values")
        if not isinstance(values, dict):
            raise ValueError("Ajustes inválidos.")
        allowed = {"accent", "glassOpacity", "blurIntensity"}
        if set(values) - allowed:
            raise ValueError("Ajuste desconhecido.")
        current = config()
        overrides = dict(current.get("overrides") or {})
        for key, value in values.items():
            if key == "accent":
                if value is not None and (not isinstance(value, str) or not HEX.fullmatch(value)):
                    raise ValueError("Destaque precisa estar em #RRGGBB.")
            elif value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1):
                raise ValueError(f"{key} precisa estar entre 0 e 1.")
            overrides[key] = value
        update_config({"overrides": overrides})
    elif operation == "workspace_style":
        style = payload.get("style")
        if style not in ("icons", "dots"):
            raise ValueError("Estilo de workspace inválido.")
        update_config({"workspaceStyle": style})
    elif operation == "do_not_disturb":
        enabled = payload.get("enabled")
        if not isinstance(enabled, bool):
            raise ValueError("Não perturbe precisa ser verdadeiro ou falso.")
        update_config({"doNotDisturb": enabled})
    elif operation == 'preferences':
        changes = payload.get('values')
        if not isinstance(changes, dict) or set(changes) - {'modules', 'animations', 'island', 'maxVisibleWorkspaces', 'shell', 'corners', 'sync', 'wallpapers'}:
            raise ValueError('Preferência desconhecida.')
        current = config()
        result = {}
        for key, values in changes.items():
            if key in ('shell', 'corners', 'sync'):
                fields = {'shell': {'islandVisible'}, 'corners': {'enabled', 'radius'}, 'sync': {'portal', 'kitty', 'hyprland', 'wallpaper'}}[key]
                if not isinstance(values, dict) or set(values) - fields: raise ValueError('Preferência desconhecida.')
                for name, value in values.items():
                    if name == 'radius':
                        if type(value) is not int or not 1 <= value <= 48: raise ValueError('Raio deve ser de 1 a 48.')
                    elif type(value) is not bool: raise ValueError('Ajuste exige verdadeiro/falso.')
            elif key == 'wallpapers':
                if not isinstance(values, dict): raise ValueError('Associações inválidas.')
                for theme_id, path in values.items():
                    require_theme(theme_id)
                    if not isinstance(path, str) or len(path) > 4096 or '\x00' in path: raise ValueError('Caminho inválido.')
                    if path:
                        candidate = Path(path).expanduser().resolve()
                        if not candidate.is_file() or not candidate.is_relative_to((Path.home() / 'Pictures/Wallpapers').resolve()):
                            raise ValueError('Escolha uma imagem de ~/Pictures/Wallpapers.')
            elif key == 'modules':
                if not isinstance(values, dict) or set(values) - set(MODULES) or any(type(v) is not bool for v in values.values()):
                    raise ValueError('Módulo inválido.')
            elif key == 'animations':
                if not isinstance(values, dict) or set(values) - {'enabled', 'scale'}:
                    raise ValueError('Animação inválida.')
                if 'enabled' in values and type(values['enabled']) is not bool: raise ValueError('Animação exige verdadeiro/falso.')
                if 'scale' in values and (type(values['scale']) not in (int, float) or not .5 <= values['scale'] <= 2):
                    raise ValueError('Duração deve estar entre 0,5 e 2.')
            elif key == 'island':
                limits = {'topMargin': (0, 80), 'hoverExpandDelayMs': (0, 1000)}
                if not isinstance(values, dict) or set(values) - set(limits): raise ValueError('Ajuste da ilha inválido.')
                for name, value in values.items():
                    if type(value) is not int or not limits[name][0] <= value <= limits[name][1]: raise ValueError('Ajuste da ilha fora do intervalo.')
            else:
                if type(values) is not int or not 1 <= values <= 12: raise ValueError('Limite de workspaces deve ser de 1 a 12.')
                result[key] = values
                continue
            result[key] = {**current.get(key, {}), **values}
        # Validar tudo antes de gravar; preserva outros campos e preferências futuras.
        update_config(result)
    else:
        raise ValueError("Operação desconhecida.")
    return snapshot()


def main():
    try:
        operation = sys.argv[1]
        payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = {"ok": True, **perform(operation, payload)}
    except (IndexError, ValueError, OSError, json.JSONDecodeError) as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
