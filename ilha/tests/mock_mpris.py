#!/usr/bin/env python3
"""Player MPRIS temporário para validar a ilha sem áudio nem pacote extra."""

import os
import signal
from pathlib import Path

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


BUS_NAME = "org.mpris.MediaPlayer2.ilha_test"
OBJECT_PATH = "/org/mpris/MediaPlayer2"
ROOT_INTERFACE = "org.mpris.MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

ART = Path("/tmp/ilha-mpris-cover.svg")
ART.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">'
    '<rect width="96" height="96" rx="16" fill="#5d547e"/>'
    '<circle cx="48" cy="48" r="29" fill="#c9bbec"/>'
    '<circle cx="48" cy="48" r="9" fill="#5d547e"/>'
    '</svg>', encoding="utf-8"
)


class MockPlayer(dbus.service.Object):
    def __init__(self, bus):
        self.track = 1
        self.status = "Playing"
        self.props = {
            ROOT_INTERFACE: {
                "Identity": dbus.String("Player de teste"),
                "DesktopEntry": dbus.String(os.environ.get("ILHA_TEST_DESKTOP_ENTRY", "mpv")),
                "CanQuit": dbus.Boolean(False),
                "CanRaise": dbus.Boolean(False),
                "HasTrackList": dbus.Boolean(False),
                "SupportedUriSchemes": dbus.Array([], signature="s"),
                "SupportedMimeTypes": dbus.Array([], signature="s"),
            },
            PLAYER_INTERFACE: {
                "PlaybackStatus": dbus.String(self.status),
                "Metadata": self.metadata(),
                "CanControl": dbus.Boolean(True),
                "CanPlay": dbus.Boolean(True),
                "CanPause": dbus.Boolean(True),
                "CanGoNext": dbus.Boolean(True),
                "CanGoPrevious": dbus.Boolean(True),
                "CanSeek": dbus.Boolean(False),
                "Volume": dbus.Double(1),
                "Rate": dbus.Double(1),
                "MinimumRate": dbus.Double(1),
                "MaximumRate": dbus.Double(1),
                "Shuffle": dbus.Boolean(False),
                "LoopStatus": dbus.String("None"),
                "Position": dbus.Int64(0),
            },
        }
        super().__init__(bus, OBJECT_PATH)

    def metadata(self):
        return dbus.Dictionary({
            "mpris:trackid": dbus.ObjectPath(f"/org/mpris/MediaPlayer2/track/{self.track}"),
            "mpris:artUrl": dbus.String(ART.as_uri()),
            "mpris:length": dbus.Int64(150_000_000),
            "xesam:title": dbus.String(f"Faixa de teste {self.track}"),
            "xesam:artist": dbus.Array(["Ilha"], signature="s"),
            "xesam:album": dbus.String("Integração MPRIS"),
        }, signature="sv")

    @dbus.service.method(PROPERTIES_INTERFACE, in_signature="ss", out_signature="v")
    def Get(self, interface, name):
        return self.props[interface][name]

    @dbus.service.method(PROPERTIES_INTERFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        return dbus.Dictionary(self.props.get(interface, {}), signature="sv")

    @dbus.service.method(PROPERTIES_INTERFACE, in_signature="ssv")
    def Set(self, interface, name, value):
        if interface == PLAYER_INTERFACE and name == "Volume":
            self.props[interface][name] = value
            self.PropertiesChanged(interface, {name: value}, [])

    @dbus.service.signal(PROPERTIES_INTERFACE, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def PlayPause(self):
        self.status = "Paused" if self.status == "Playing" else "Playing"
        self.props[PLAYER_INTERFACE]["PlaybackStatus"] = dbus.String(self.status)
        self.PropertiesChanged(PLAYER_INTERFACE, {"PlaybackStatus": dbus.String(self.status)}, [])
        print(f"estado={self.status}", flush=True)

    @dbus.service.method(PLAYER_INTERFACE)
    def Play(self):
        if self.status != "Playing":
            self.PlayPause()

    @dbus.service.method(PLAYER_INTERFACE)
    def Pause(self):
        if self.status == "Playing":
            self.PlayPause()

    @dbus.service.method(PLAYER_INTERFACE)
    def Next(self):
        self.track += 1
        self.props[PLAYER_INTERFACE]["Metadata"] = self.metadata()
        self.PropertiesChanged(PLAYER_INTERFACE, {"Metadata": self.props[PLAYER_INTERFACE]["Metadata"]}, [])
        print(f"faixa={self.track}", flush=True)

    @dbus.service.method(PLAYER_INTERFACE)
    def Previous(self):
        self.track = max(1, self.track - 1)
        self.props[PLAYER_INTERFACE]["Metadata"] = self.metadata()
        self.PropertiesChanged(PLAYER_INTERFACE, {"Metadata": self.props[PLAYER_INTERFACE]["Metadata"]}, [])
        print(f"faixa={self.track}", flush=True)


def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(BUS_NAME, bus, do_not_queue=True)
    player = MockPlayer(bus)
    loop = GLib.MainLoop()
    signal.signal(signal.SIGINT, lambda *_: loop.quit())
    signal.signal(signal.SIGTERM, lambda *_: loop.quit())
    print(f"pronto={BUS_NAME}", flush=True)
    loop.run()


if __name__ == "__main__":
    main()
