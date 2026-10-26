#!/usr/bin/env python3
"""Observador D-Bus do KDE Connect. Não envia mensagens, ações ou pedidos de pareamento."""
import json
import os
import re
import sys

SERVICE = 'org.kde.kdeconnect'
BASE = '/modules/kdeconnect'
DEVICE = SERVICE + '.device'
PROPERTIES = 'org.freedesktop.DBus.Properties'


def plain(value):
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    # D-Bus bool é uma subclasse de int.
    if type(value).__name__ == 'Boolean':
        return bool(value)
    if isinstance(value, int):
        return int(value)
    return str(value) if value is not None else None


def device_record(identifier, properties, battery=None, plugins=()):
    battery = battery or {}
    charge = int(battery.get('charge', -1))
    return {'id': str(identifier), 'name': str(properties.get('name', 'Celular'))[:100],
            'type': str(properties.get('type', 'phone')),
            'reachable': bool(properties.get('isReachable')),
            'paired': bool(properties.get('isPaired')),
            'charge': charge if battery.get('hasBattery') and 0 <= charge <= 100 else None,
            'charging': bool(battery.get('isCharging')), 'plugins': list(map(str, plugins))}


class Monitor:
    def __init__(self, bus, glib, service=SERVICE):
        self.bus, self.glib, self.service = bus, glib, service
        self.devices = {}
        self.scheduled = False

    def emit(self, kind, **data):
        print(json.dumps({'kind': kind, **data}, ensure_ascii=False), flush=True)

    def properties(self, path, interface):
        obj = self.bus.get_object(self.service, path, introspect=False)
        return plain(obj.GetAll(interface, dbus_interface=PROPERTIES, timeout=2))

    def refresh(self):
        self.scheduled = False
        devices, ready = {}, False
        try:
            # Não autoativar o daemon se o usuário o tiver encerrado.
            if self.bus.name_has_owner(self.service):
                obj = self.bus.get_object(self.service, BASE, introspect=False)
                identifiers = obj.devices(False, True, dbus_interface=SERVICE + '.daemon', timeout=2)
                ready = True
                for identifier in list(identifiers)[:16]:
                    identifier = str(identifier)
                    path = BASE + '/devices/' + identifier
                    try:
                        props = self.properties(path, DEVICE)
                        battery, plugins = {}, []
                        if props.get('isPaired') and props.get('isReachable'):
                            device = self.bus.get_object(self.service, path, introspect=False)
                            plugins = list(device.loadedPlugins(dbus_interface=DEVICE, timeout=2))
                            if 'kdeconnect_battery' in plugins:
                                battery = self.properties(path + '/battery', DEVICE + '.battery')
                        devices[identifier] = device_record(identifier, props, battery, plugins)
                    except Exception:
                        continue
        except Exception:
            pass
        self.devices = devices
        native_owned = False
        try:
            owner = self.bus.get_name_owner('org.freedesktop.Notifications')
            daemon = self.bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspect=False)
            pid = daemon.GetConnectionUnixProcessID(owner, dbus_interface='org.freedesktop.DBus', timeout=2)
            native_owned = int(pid) == os.getppid()
        except Exception:
            pass
        self.emit('snapshot', ready=ready, devices=list(devices.values()), nativeNotificationsOwned=native_owned)
        return False

    def schedule(self, *_):
        if not self.scheduled:
            self.scheduled = True
            self.glib.timeout_add(150, self.refresh)

    def notice(self, identifier, public_id):
        if not re.fullmatch(r'[A-Za-z0-9_]+', str(public_id)):
            return
        try:
            props = self.properties(BASE + '/devices/' + identifier + '/notifications/' + str(public_id),
                                    DEVICE + '.notifications.notification')
            # KDE Connect emite ready antes de notificationPosted; não extrair conteúdo de logs.
            self.emit('notice', deviceId=identifier, id=str(public_id),
                      appName=str(props.get('appName', 'Celular'))[:100],
                      title=str(props.get('title') or props.get('ticker') or 'Notificação')[:200],
                      text=str(props.get('text', ''))[:1000], silent=bool(props.get('silent')))
        except Exception:
            pass

    def signal(self, *args, path='', member='', **_):
        match = re.match(re.escape(BASE) + r'/devices/([^/]+)(?:/|$)', str(path))
        identifier = match.group(1) if match else None
        device = self.devices.get(identifier, {})
        if identifier and device.get('paired') and device.get('reachable'):
            if member == 'callReceived' and len(args) == 3 and str(args[0]) in ('callReceived', 'missedCall'):
                self.emit('call', deviceId=identifier, event=str(args[0]),
                          contact=str(args[2] or args[1] or 'Contato desconhecido')[:150])
            elif member in ('notificationPosted', 'notificationUpdated') and args:
                self.notice(identifier, args[0])
            elif member == 'ready' and '/notifications/' in str(path):
                # A versão instalada também anuncia atualizações no próprio objeto.
                self.notice(identifier, str(path).rsplit('/', 1)[-1])
            elif member == 'notificationRemoved' and args:
                self.emit('noticeRemoved', deviceId=identifier, id=str(args[0]))
            elif member == 'allNotificationsRemoved':
                self.emit('noticeRemoved', deviceId=identifier, id='')
        if member in ('deviceAdded', 'deviceRemoved', 'deviceVisibilityChanged', 'deviceListChanged',
                      'reachableChanged', 'pairStateChanged', 'pluginsChanged', 'nameChanged', 'refreshed'):
            self.schedule()


def main():
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    monitor = Monitor(bus, GLib)
    bus.add_signal_receiver(monitor.signal, bus_name=SERVICE,
                            path_keyword='path', member_keyword='member')
    bus.add_signal_receiver(monitor.schedule, signal_name='NameOwnerChanged',
        dbus_interface='org.freedesktop.DBus', arg0=SERVICE)
    bus.add_signal_receiver(monitor.schedule, signal_name='NameOwnerChanged',
        dbus_interface='org.freedesktop.DBus', arg0='org.freedesktop.Notifications')
    monitor.refresh()
    # Reconciliar é útil se o daemon reiniciar ou um plugin não emitir PropertiesChanged.
    GLib.timeout_add_seconds(30, lambda: (monitor.schedule(), True)[1])
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()
