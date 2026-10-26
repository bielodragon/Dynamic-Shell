pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    property string screenName: ""
    property bool opened: false
    property var state: ({})
    property bool busy: false
    property string message: ""
    function open(name) { screenName = name; opened = true; refresh(); }
    function close() { opened = false; }
    function refresh() { if (!reader.running) reader.running = true; }
    function action(name, value, confirmed) {
        if (busy) return;
        busy = true; message = "";
        writer.exec(["python3", Quickshell.shellPath("scripts/system_controls.py"), "action",
            JSON.stringify({ name, value, confirmed: confirmed === true })]);
    }
    Process {
        id: reader
        command: ["python3", Quickshell.shellPath("scripts/system_controls.py"), "snapshot"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    if (response.ok) root.state = response.state;
                    else root.message = response.error;
                } catch (_) { root.message = "Não foi possível ler os controles."; }
            }
        }
    }
    Process {
        id: writer
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    root.message = response.ok ? "" : response.error;
                } catch (_) { root.message = "O controle não respondeu."; }
                root.busy = false;
                root.refresh();
            }
        }
    }
    Timer { interval: 3000; repeat: true; running: root.opened; onTriggered: root.refresh() }
    IpcHandler {
        target: "controlCenter"
        function open(screenName: string): void { root.open(screenName); }
        function close(): void { root.close(); }
        function status(): string { return JSON.stringify({ opened: root.opened, screenName: root.screenName, state: root.state, busy: root.busy }); }
    }
}
