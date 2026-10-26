#!/usr/bin/env python3
"""Lê configuração local do OBS sem enviar sua senha ao QML ou aos logs."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys


def authentication(password, salt, challenge):
    def digest(value):
        return base64.b64encode(hashlib.sha256(value.encode()).digest()).decode()
    return digest(digest(password + salt) + challenge)


def main():
    default = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'obs-studio/plugin_config/obs-websocket/config.json'
    path = Path(os.environ.get('ILHA_OBS_CONFIG', default))
    try:
        config = json.loads(path.read_text())
        port = int(config.get('server_port', 4455))
        if not 1 <= port <= 65535:
            raise ValueError()
        result = {'enabled': bool(config.get('server_enabled')), 'port': port}
        if len(sys.argv) == 3:
            result['authentication'] = authentication(config.get('server_password', ''), sys.argv[1], sys.argv[2])
    except (OSError, ValueError, TypeError):
        result = {'enabled': False, 'port': 4455}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
