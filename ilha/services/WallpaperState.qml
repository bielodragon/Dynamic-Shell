pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property var options: ThemeStore.config.wallpaper || ({})
    readonly property string path: options.path || ""
    readonly property bool enabled: !!options.enabled && path.length > 0
    readonly property string source: path ? "file://" + path.split("/").map(encodeURIComponent).join("/") : ""
    readonly property bool gif: path.toLowerCase().endsWith(".gif")
    readonly property bool onBattery: DeviceState.batteries.some(b => b.status === "Discharging")
    readonly property bool paused: !!options.paused || (options.pauseOnBattery !== false && onBattery)
        || (options.pauseOnPerformance !== false && !!DeviceState.controls.performance)
    property bool busy: false
    property string message: ""
    property string requestId: ""
    property var surfaces: ({})
    readonly property bool ready: enabled && Quickshell.screens.length > 0
        && Array.from(Quickshell.screens).every(screen => surfaces[screen.name] && surfaces[screen.name].ready)
    onPathChanged: surfaces = ({})
    onEnabledChanged: if (!enabled) surfaces = ({})
    function select(path) {
        if (busy) return "";
        busy = true; message = "";
        requestId = Date.now().toString() + "-" + Math.random().toString(36).slice(2);
        ThemeStore.run("animated_wallpaper",{path:path});
        return requestId;
    }
    function stop() { message=""; ThemeStore.setPreferences({wallpaper:{enabled:false}}); }
    function pause(value) { ThemeStore.setPreferences({wallpaper:{paused:value}}); }
    function report(name,data) { if (enabled) { const next=Object.assign({},surfaces);next[name]=data;surfaces=next; } }
    function forget(name) { const next=Object.assign({},surfaces);delete next[name];surfaces=next; }
    function failed(reason) {
        if (!enabled || !path) return;
        stop();
        message = "Não foi possível reproduzir o wallpaper: " + reason;
    }
    Connections {
        target: ThemeStore
        function onOperationFinished(operation,ok) {
            if (operation !== "animated_wallpaper") return;
            root.busy=false;
            if (!ok) root.message=ThemeStore.message;
        }
    }
    IpcHandler {
        target: "wallpaper"
        function select(path: string): string { return root.select(path); }
        function stop(): void { root.stop(); }
        function pause(paused: bool): void { root.pause(paused); }
        function configure(options: string): void {
            try { root.message=""; ThemeStore.setPreferences({wallpaper:JSON.parse(options)}); }
            catch (_) { root.message="Ajustes de wallpaper inválidos."; }
        }
        function status(): string { return JSON.stringify({enabled:root.enabled,path:root.path,paused:root.paused,
            busy:root.busy,ready:root.ready,message:root.message,requestId:root.requestId,surfaces:root.surfaces,options:root.options}); }
    }
}
