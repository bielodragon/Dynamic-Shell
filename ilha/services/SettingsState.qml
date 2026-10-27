pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    property bool opened: false
    property string page: "modules"
    property string message: ""
    property bool hyprmodAvailable: false
    function open(tab) { page = tab || "modules"; opened = true; check(); }
    function check() { if (!external.running) external.exec(["python3", Quickshell.shellPath("scripts/external_apps.py"), "check"]); }
    function launchHyprmod() { message = ""; if (!external.running) external.exec(["python3", Quickshell.shellPath("scripts/external_apps.py"), "launch"]); }
    Process {
        id: external
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    if (response.ok) { root.hyprmodAvailable = response.available; root.message = ""; }
                    else root.message = response.error;
                } catch (_) { root.message = "Não foi possível abrir o HyprMod."; }
            }
        }
    }
    IpcHandler {
        target: "settings"
        function open(page: string): void { root.open(["modules", "appearance", "themes", "wallpaper"].includes(page) ? page : "modules"); }
        function close(): void { root.opened = false; }
        function status(): string { return JSON.stringify({ opened: root.opened, page: root.page, modules: Preferences.modules,
            animationsEnabled: Preferences.animationsEnabled, animationScale: Preferences.animationScale,
            hyprmodAvailable: root.hyprmodAvailable, message: root.message }); }
    }
}
