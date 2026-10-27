#!/usr/bin/env python3
"""Controles com argumentos fechados; não executa comandos fornecidos pelo usuário."""
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ENV = dict(os.environ, LC_ALL='C', NO_COLOR='1')


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, env=ENV, timeout=10)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or 'Comando indisponível.').strip()[:240])
    return result.stdout.strip()


def network():
    import dbus
    bus = dbus.SystemBus()
    props = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager'),
                           'org.freedesktop.DBus.Properties')
    state = props.GetAll('org.freedesktop.NetworkManager', timeout=2)
    name = ''
    connection = str(state.get('PrimaryConnection', '/'))
    if connection != '/':
        active = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', connection),
                                'org.freedesktop.DBus.Properties')
        name = str(active.Get('org.freedesktop.NetworkManager.Connection.Active', 'Id', timeout=2))
    return {'available': True, 'wifi': bool(state['WirelessEnabled']),
            'wifiHardware': bool(state['WirelessHardwareEnabled']),
            'wwan': bool(state['WwanEnabled']), 'connection': name}


def bluetooth():
    import dbus
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
    objects = manager.GetManagedObjects(timeout=2)
    adapters = [{'path': str(path), 'powered': bool(interfaces['org.bluez.Adapter1']['Powered'])}
                for path, interfaces in objects.items() if 'org.bluez.Adapter1' in interfaces]
    count = sum(bool(interfaces.get('org.bluez.Device1', {}).get('Connected')) for interfaces in objects.values())
    return {'available': bool(adapters), 'powered': any(item['powered'] for item in adapters),
            'adapters': adapters, 'connected': count}


def audio():
    value = run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'])
    match = re.search(r'Volume:\s*([0-9.]+)', value)
    if not match: raise RuntimeError('Saída de áudio não encontrada.')
    return {'available': True, 'volume': round(float(match[1]) * 100), 'muted': '[MUTED]' in value}


def brightness():
    value = run(['brightnessctl', '--class=backlight', '-m']).splitlines()[0].split(',')
    if value[1] != 'backlight': raise RuntimeError('Sem backlight ajustável.')
    return {'available': True, 'value': int(value[3].rstrip('%')), 'device': value[0]}


def profiles():
    available = re.findall(r'^\s*\*?\s*(balanced|power-saver|performance):', run(['powerprofilesctl', 'list']), re.M)
    return {'available': bool(available), 'profiles': available, 'current': run(['powerprofilesctl', 'get'])}


def battery():
    from device_metrics import battery as device_battery
    return device_battery()


def capabilities():
    import dbus
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1'),
                             'org.freedesktop.login1.Manager')
    return {'available': True, 'poweroff': str(manager.CanPowerOff(timeout=2)) in ('yes', 'challenge'),
            'reboot': str(manager.CanReboot(timeout=2)) in ('yes', 'challenge'),
            'suspend': str(manager.CanSuspend(timeout=2)) in ('yes', 'challenge'),
            'lock': bool(shutil.which('omarchy') or shutil.which('hyprlock') or shutil.which('swaylock')),
            'logout': bool(shutil.which('uwsm'))}


def snapshot():
    sources = {'network': network, 'bluetooth': bluetooth, 'audio': audio, 'brightness': brightness,
               'profiles': profiles, 'battery': battery, 'session': capabilities}
    def collect(item):
        key, function = item
        try: return key, function()
        except Exception as error: return key, {'available': False, 'error': str(error)[:240]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        return dict(pool.map(collect, sources.items()))


def boolean(value):
    if type(value) is not bool: raise ValueError('Esperado ligado/desligado.')
    return value


def percent(value, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= 100:
        raise ValueError('Percentual fora do intervalo permitido.')
    return str(round(value)) + '%'


def set_bluetooth(enabled):
    import dbus
    state = bluetooth()
    if not state['available']: raise RuntimeError('Nenhum adaptador Bluetooth disponível.')
    bus = dbus.SystemBus()
    for adapter in state['adapters']:
        props = dbus.Interface(bus.get_object('org.bluez', adapter['path']), 'org.freedesktop.DBus.Properties')
        props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(enabled), timeout=3)


def airplane(enabled):
    # Guardar os estados anteriores evita ligar um rádio que já estava desligado.
    directory = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / 'ilha'
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / 'radios.json'
    if enabled:
        net = network()
        try: blue = bluetooth()
        except Exception: blue = {'available': False, 'adapters': []}
        if not path.exists():
            saved = {'wifi': net['wifi'], 'wwan': net['wwan'], 'adapters': blue['adapters']}
            path.write_text(json.dumps(saved))
        try:
            run(['nmcli', 'radio', 'all', 'off'])
            if blue['available']: set_bluetooth(False)
        except Exception:
            # Tentar restaurar sem esconder a falha original. O arquivo permite nova tentativa.
            try: airplane(False)
            except Exception: pass
            raise
    else:
        if not path.exists(): raise RuntimeError('Não há estados de rádio salvos pela Ilha para restaurar.')
        import dbus
        saved = json.loads(path.read_text())
        run(['nmcli', 'radio', 'wifi', 'on' if saved['wifi'] else 'off'])
        run(['nmcli', 'radio', 'wwan', 'on' if saved['wwan'] else 'off'])
        bus = dbus.SystemBus()
        for adapter in saved['adapters']:
            props = dbus.Interface(bus.get_object('org.bluez', adapter['path']), 'org.freedesktop.DBus.Properties')
            props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(adapter['powered']), timeout=3)
        path.unlink()


def action(name, value=None, confirmed=False):
    if name == 'wifi': run(['nmcli', 'radio', 'wifi', 'on' if boolean(value) else 'off'])
    elif name == 'bluetooth': set_bluetooth(boolean(value))
    elif name == 'airplane': airplane(boolean(value))
    elif name == 'volume': run(['wpctl', 'set-volume', '--limit', '1.0', '@DEFAULT_AUDIO_SINK@', percent(value)])
    elif name == 'mute': run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', '1' if boolean(value) else '0'])
    elif name == 'brightness': run(['brightnessctl', '--class=backlight', 'set', percent(value, 1)])
    elif name == 'profile':
        if value not in profiles()['profiles']: raise ValueError('Perfil não oferecido pelo sistema.')
        run(['powerprofilesctl', 'set', value])
    elif name in ('poweroff', 'reboot', 'suspend', 'lock', 'logout'):
        if confirmed is not True: raise ValueError('Confirme a ação no painel.')
        if not capabilities().get(name): raise RuntimeError('Ação de sessão indisponível.')
        if name in ('poweroff', 'reboot', 'suspend'): run(['systemctl', name])
        elif name == 'logout': run(['uwsm', 'stop'])
        elif shutil.which('omarchy'): run(['omarchy', 'system', 'lock'])
        else:
            executable = shutil.which('hyprlock') or shutil.which('swaylock')
            subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    else: raise ValueError('Ação desconhecida.')


def main():
    try:
        if len(sys.argv) == 2 and sys.argv[1] == 'snapshot':
            data = snapshot()
            runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
            data['airplaneManaged'] = (runtime / 'ilha/radios.json').exists()
            data['airplane'] = (data['airplaneManaged']
                and not data['network'].get('wifi') and not data['network'].get('wwan')
                and not data['bluetooth'].get('powered'))
            result = {'ok': True, 'state': data}
        elif len(sys.argv) == 3 and sys.argv[1] == 'action':
            payload = json.loads(sys.argv[2])
            action(payload['name'], payload.get('value'), payload.get('confirmed', False))
            result = {'ok': True}
        else: raise ValueError('Operação inválida.')
    except Exception as error:
        result = {'ok': False, 'error': str(error)[:300]}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__': main()
