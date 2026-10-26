pragma Singleton
import QtQuick
import QtWebSockets
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property bool integrationEnabled: Preferences.enabled("privacy")
    onIntegrationEnabledChanged: {
        if (integrationEnabled) configWorker.running = true;
        else { socket.active = false; enabled = false; reset(); }
    }
    property bool enabled: false
    property int port: 4455
    property bool identified: false
    property bool available: false
    property bool recording: false
    property bool paused: false
    property real duration: 0
    property bool changingScenes: false
    property string pending: ""
    property int sequence: 0
    property real requestedAt: 0

    function snapshot() {
        return { enabled, available, recording, paused, durationMs: duration };
    }
    function reset() {
        identified = false; available = false; recording = false; paused = false;
        duration = 0; pending = ""; changingScenes = false;
    }
    function send(op, data) { socket.sendTextMessage(JSON.stringify({ op, d: data })); }
    function identify(authentication) {
        if (socket.status !== WebSocket.Open) return;
        const data = { rpcVersion: 1, eventSubscriptions: 66 };
        if (authentication) data.authentication = authentication;
        send(1, data);
    }
    function query() {
        if (!identified || changingScenes || pending) return;
        pending = "ilha-record-" + (++sequence);
        requestedAt = Date.now();
        send(6, { requestType: "GetRecordStatus", requestId: pending });
    }
    Component.onCompleted: if (integrationEnabled) configWorker.running = true
    Process {
        id: configWorker
        command: ["python3", Quickshell.shellPath("scripts/obs_config.py")]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    if (!root.integrationEnabled) return;
                    const data = JSON.parse(text);
                    if (root.port !== data.port || !data.enabled) { socket.active = false; root.reset(); }
                    root.port = data.port;
                    root.enabled = data.enabled;
                    if (root.enabled && socket.status !== WebSocket.Open && socket.status !== WebSocket.Connecting)
                        socket.active = true;
                } catch (_) { root.enabled = false; socket.active = false; root.reset(); }
            }
        }
    }
    Process {
        id: authWorker
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.identify(JSON.parse(text).authentication); }
                catch (_) { socket.active = false; root.reset(); }
            }
        }
    }
    WebSocket {
        id: socket
        url: "ws://127.0.0.1:" + root.port
        active: false
        onStatusChanged: function(status) {
            if (status === WebSocket.Error || status === WebSocket.Closed) {
                root.reset();
                active = false;
            }
        }
        onTextMessageReceived: message => {
            try {
                const packet = JSON.parse(message), data = packet.d || {};
                if (packet.op === 0) {
                    if (data.authentication) {
                        authWorker.exec(["python3", Quickshell.shellPath("scripts/obs_config.py"),
                            data.authentication.salt, data.authentication.challenge]);
                    } else root.identify("");
                } else if (packet.op === 2) {
                    root.identified = true;
                    root.query();
                } else if (packet.op === 7 && data.requestId === root.pending) {
                    root.pending = "";
                    if (!data.requestStatus.result) { socket.active = false; root.reset(); return; }
                    const response = data.responseData;
                    root.available = true;
                    root.recording = response.outputActive === true;
                    root.paused = response.outputPaused === true;
                    root.duration = Math.max(0, Number(response.outputDuration) || 0);
                } else if (packet.op === 5) {
                    if (data.eventType === "CurrentSceneCollectionChanging") root.changingScenes = true;
                    if (data.eventType === "CurrentSceneCollectionChanged") root.changingScenes = false;
                    if (data.eventType === "RecordStateChanged" || data.eventType === "CurrentSceneCollectionChanged") root.query();
                }
            } catch (_) { socket.active = false; root.reset(); }
        }
    }
    Timer {
        interval: 5000; repeat: true; running: root.integrationEnabled
        onTriggered: if (!configWorker.running) configWorker.running = true
    }
    // O tempo vem do OBS; pausa e retomada não dependem de um relógio estimado.
    Timer {
        interval: 1000; repeat: true; running: root.identified
        onTriggered: {
            if (root.pending && Date.now() - root.requestedAt > 3000) {
                socket.active = false; root.reset();
            } else root.query();
        }
    }
}
