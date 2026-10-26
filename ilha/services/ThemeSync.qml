pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property bool loaded: true
    property string message: ""
    property var pending: null
    function schedule() { delay.restart(); }
    function start() {
        if (worker.running || !pending) return;
        const job = pending; pending = null;
        worker.exec(["python3", Quickshell.shellPath("scripts/theme_sync.py"), JSON.stringify(job)]);
    }
    Timer {
        id: delay; interval: 250
        onTriggered: {
            const options = ThemeStore.config.sync || {};
            if (!ThemeStore.ready || !ThemeStore.selectedTheme || !Object.keys(options).some(key => options[key])) return;
            root.pending = {theme:ThemeStore.selectedTheme,config:ThemeStore.config}; root.start();
        }
    }
    Process {
        id: worker
        stdout: StdioCollector {
            onStreamFinished: {
                try { const response = JSON.parse(text); root.message = (response.errors || []).join(" · "); }
                catch (_) { root.message = "Não foi possível sincronizar o tema."; }
            }
        }
        onExited: Qt.callLater(root.start)
    }
    IpcHandler {
        target: "theme-sync"
        function apply(): void { root.schedule(); }
        function status(): string { return JSON.stringify({busy:worker.running,message:root.message}); }
    }
}
