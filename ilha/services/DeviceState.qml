pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property var preferences: ThemeStore.config.monitoring || ({})
    readonly property bool showMetrics: !!preferences.metrics
    readonly property bool showFps: !!preferences.fps
    readonly property bool showBattery: preferences.battery !== false
    property var data: ({})
    readonly property var batteries: (data.battery || {}).batteries || []
    property var controls: ({})
    onControlsChanged: Preferences.performanceMode = !!controls.performance
    property bool busy: false
    property string message: ""
    property var pending: null
    function action(name, value) {
        if (busy || worker.running) { pending = {name:name,value:value}; return; }
        busy = true; message = "";
        worker.exec(["python3",Quickshell.shellPath("scripts/monitor_controls.py"),name,JSON.stringify(value)]);
    }
    function metrics(value) { ThemeStore.setPreferences({monitoring:{metrics:value}}); }
    function fps(value) {
        if (!controls.mangoAvailable) { message = "Instale mangohud para mostrar FPS nos jogos."; return; }
        ThemeStore.setPreferences({monitoring:{fps:value}});
    }
    onShowFpsChanged: if (ThemeStore.ready) action("hud", showFps)
    Process {
        id: observer
        command: ["python3",Quickshell.shellPath("scripts/device_metrics.py")].concat(root.showMetrics ? ["--metrics"] : [])
        running: true
        onCommandChanged: if (running) { running = false; restart.restart(); }
        stdout: SplitParser { onRead: line => { try { root.data = JSON.parse(line); } catch (_) {} } }
        onExited: { root.data = ({}); restart.restart(); }
    }
    Timer { id: restart; interval: 100; onTriggered: observer.running = true }
    Process {
        id: worker
        onExited: Qt.callLater(() => { if (root.pending) { const job=root.pending; root.pending=null; root.action(job.name,job.value); } })
        stdout: StdioCollector {
            onStreamFinished: {
                try { const response=JSON.parse(text); if (response.ok) { root.controls=response.state; root.message=""; } else root.message=response.error; }
                catch (_) { root.message="O controle de desempenho não respondeu."; }
                root.busy=false;
            }
        }
    }
    Component.onCompleted: action("status", null)
    Timer { interval: 3000; repeat: true; running: ControlCenterState.opened; onTriggered: if (!root.busy) root.action("status",null) }
    IpcHandler {
        target: "device"
        function status(): string { return JSON.stringify({data:root.data,controls:root.controls,metrics:root.showMetrics,fps:root.showFps,busy:root.busy,message:root.message}); }
        function setMetrics(enabled: bool): void { root.metrics(enabled); }
        function setFps(enabled: bool): void { root.fps(enabled); }
        function setPerformance(enabled: bool): void { root.action("performance",enabled); }
    }
}
