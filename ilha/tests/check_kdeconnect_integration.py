#!/usr/bin/env python3
"""Teste em barramento D-Bus privado: nunca pareia nem envia algo ao celular real."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = '/modules/kdeconnect'
SERVICE = 'org.kde.kdeconnect'
DEVICE = SERVICE + '.device'
CONTROL = 'org.example.IlhaTest'


def serve():
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(SERVICE, bus, do_not_queue=True)
    desktop_name = dbus.service.BusName('org.freedesktop.Notifications', bus, do_not_queue=True)

    class Props(dbus.service.Object):
        def __init__(self, path, values):
            super().__init__(bus, path)
            self.values = values

        @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='s', out_signature='a{sv}')
        def GetAll(self, interface):
            return self.values

    class Device(Props):
        @dbus.service.method(DEVICE, out_signature='as')
        def loadedPlugins(self):
            return ['kdeconnect_battery', 'kdeconnect_notifications', 'kdeconnect_telephony']

        @dbus.service.signal(DEVICE, signature='b')
        def reachableChanged(self, reachable): pass

    class Battery(Props):
        @dbus.service.signal(DEVICE + '.battery', signature='bi')
        def refreshed(self, charging, charge): pass

    class Notifications(dbus.service.Object):
        @dbus.service.signal(DEVICE + '.notifications', signature='s')
        def notificationPosted(self, public_id): pass

        @dbus.service.signal(DEVICE + '.notifications', signature='s')
        def notificationUpdated(self, public_id): pass

        @dbus.service.signal(DEVICE + '.notifications', signature='s')
        def notificationRemoved(self, public_id): pass

    class Notice(Props):
        @dbus.service.signal(DEVICE + '.notifications.notification')
        def ready(self): pass

    class Telephony(dbus.service.Object):
        @dbus.service.signal(DEVICE + '.telephony', signature='sss')
        def callReceived(self, event, number, contact): pass

    device = Device(BASE + '/devices/test', {'name': 'Celular de teste', 'type': 'phone',
        'isPaired': dbus.Boolean(True), 'isReachable': dbus.Boolean(True)})
    battery = Battery(BASE + '/devices/test/battery', {'charge': dbus.Int32(72),
        'hasBattery': dbus.Boolean(True), 'isCharging': dbus.Boolean(False)})
    notices = Notifications(bus, BASE + '/devices/test/notifications')
    notice = Notice(BASE + '/devices/test/notifications/1', {'appName': 'App de teste',
        'title': 'Notificação <literal>', 'text': 'Conteúdo de teste', 'silent': dbus.Boolean(False)})
    telephony = Telephony(bus, BASE + '/devices/test/telephony')

    class Daemon(dbus.service.Object):
        @dbus.service.method(SERVICE + '.daemon', in_signature='bb', out_signature='as')
        def devices(self, reachable, paired): return ['test']

        @dbus.service.method(CONTROL, in_signature='ib')
        def Battery(self, charge, charging):
            battery.values.update(charge=charge, isCharging=charging)
            battery.refreshed(charging, charge)

        @dbus.service.method(CONTROL, in_signature='s')
        def Notice(self, action):
            if action == 'remove': notices.notificationRemoved('1')
            elif action == 'update':
                notice.values['title'] = 'Notificação atualizada'
                notice.ready()
            elif action == 'silent':
                notice.values['silent'] = dbus.Boolean(True)
                notices.notificationPosted('1')
            else:
                notice.values['silent'] = dbus.Boolean(False)
                notices.notificationPosted('1')

        @dbus.service.method(CONTROL)
        def Call(self): telephony.callReceived('callReceived', '123', 'Contato de teste')

        @dbus.service.method(CONTROL, in_signature='b')
        def Reachable(self, value):
            device.values['isReachable'] = value
            device.reachableChanged(value)

        @dbus.service.method(CONTROL)
        def ReleaseDesktop(self): bus.release_name('org.freedesktop.Notifications')

    daemon = Daemon(bus, BASE)
    GLib.MainLoop().run()


def check():
    import dbus
    bus = dbus.SessionBus()
    with tempfile.TemporaryDirectory(prefix='ilha-phone-test-') as directory:
        folder = Path(directory)
        for name in ('services', 'scripts', 'components'):
            (folder / name).symlink_to(ROOT / name, target_is_directory=True)
        # ThemeStore escreve somente no diretório temporário, inclusive no teste de DND.
        config = folder / 'config'
        config.mkdir()
        env = dict(os.environ, XDG_CONFIG_HOME=str(config), QT_QPA_PLATFORM='offscreen',
                   QT_QPA_PLATFORMTHEME='generic', QT_QUICK_BACKEND='software', NO_AT_BRIDGE='1')
        (folder / 'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
ShellRoot {
    IpcHandler {
        target: "phone-test"
        function status(): string {
            return JSON.stringify({ ready: KdeConnectState.ready, devices: KdeConnectState.devices,
                current: KdeConnectState.current, dnd: NotificationState.doNotDisturb,
                nativeOwned: KdeConnectState.nativeNotificationsOwned });
        }
        function dismiss(): void { KdeConnectState.dismiss(); }
        function dnd(enabled: bool): void { NotificationState.setDoNotDisturb(enabled); }
    }
}''')
        # Temas/defaults também são lidos relativamente ao shellPath no ThemeStore.
        (folder / 'themes').symlink_to(ROOT / 'themes', target_is_directory=True)
        (folder / 'config.json').symlink_to(ROOT / 'config.json')
        with (folder / 'qml.log').open('w+') as log:
            mock = subprocess.Popen([sys.executable, __file__, '--serve'], stdout=log, stderr=log)
            process = None
            try:
                deadline = time.monotonic() + 5
                while not bus.name_has_owner(SERVICE):
                    assert time.monotonic() < deadline, 'Mock D-Bus não iniciou.'
                    time.sleep(.1)
                control = dbus.Interface(bus.get_object(SERVICE, BASE), CONTROL)
                process = subprocess.Popen(['/usr/bin/quickshell', '-p', str(folder), '--no-color'],
                                            stdout=log, stderr=log, env=env)
                def ipc(method, *args):
                    return subprocess.run(['/usr/bin/quickshell', 'ipc', '--pid', str(process.pid),
                        'call', 'phone-test', method, *args], capture_output=True, text=True, timeout=3)
                def wait_for(predicate):
                    deadline = time.monotonic() + 6
                    while time.monotonic() < deadline:
                        result = ipc('status')
                        try:
                            value = json.loads(result.stdout)
                            if predicate(value): return value
                        except ValueError: pass
                        time.sleep(.1)
                    log.seek(0)
                    raise AssertionError('Estado esperado não chegou.\n' + log.read())
                wait_for(lambda s: s['ready'] and s['devices'] and s['devices'][0]['charge'] == 72)
                control.Battery(15, True)
                wait_for(lambda s: s['devices'][0]['charge'] == 15 and s['devices'][0]['charging'])
                control.Notice('post')
                wait_for(lambda s: s['current'] and s['current']['summary'] == 'Notificação <literal>')
                control.Notice('update')
                wait_for(lambda s: s['current'] and s['current']['summary'] == 'Notificação atualizada')
                control.Notice('remove')
                wait_for(lambda s: s['current'] is None)
                control.Call()
                wait_for(lambda s: s['current'] and 'Contato de teste' in s['current']['summary'])
                ipc('dismiss')
                wait_for(lambda s: s['current'] is None)
                control.Notice('silent')
                time.sleep(.3)
                assert json.loads(ipc('status').stdout)['current'] is None
                ipc('dnd', 'true')
                wait_for(lambda s: s['dnd'])
                control.Call(); control.Notice('post')
                time.sleep(.3)
                assert json.loads(ipc('status').stdout)['current'] is None
                ipc('dnd', 'false')
                wait_for(lambda s: not s['dnd'])
                control.ReleaseDesktop()
                wait_for(lambda s: s['nativeOwned'])
                control.Call(); control.Notice('post')
                time.sleep(.3)
                assert json.loads(ipc('status').stdout)['current'] is None
                control.Reachable(False)
                wait_for(lambda s: s['devices'] and not s['devices'][0]['reachable'] and s['devices'][0]['charge'] is None)
                mock.terminate(); mock.wait(timeout=3)
                wait_for(lambda s: not s['ready'] and not s['devices'])
                log.seek(0)
                assert 'ERROR' not in log.read()
                print('OK: KDE Connect D-Bus privado → QML: bateria, carga, notificações, chamadas, DND, rota nativa sem duplicação, desconexão e daemon encerrado.')
            finally:
                if process:
                    process.terminate(); process.wait(timeout=5)
                if mock.poll() is None:
                    mock.terminate(); mock.wait(timeout=3)


if __name__ == '__main__':
    if '--serve' in sys.argv: serve()
    elif '--private' in sys.argv: check()
    else:
        raise SystemExit(subprocess.call(['dbus-run-session', '--', sys.executable, __file__, '--private']))
