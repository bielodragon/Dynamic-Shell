pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property bool enabled: Preferences.enabled("privacy")
    readonly property bool observerRunning: monitor.running
    onEnabledChanged: { monitor.running = enabled; if (!enabled) { captures = {ready: false}; preview = false; } }
    property var captures: ({ ready: false })
    property bool preview: false
    readonly property bool microphone: preview || (captures.microphone || []).length > 0
    readonly property bool camera: preview || (captures.camera || []).length > 0
    readonly property bool screenSharing: preview || (captures.screen || []).length > 0
    readonly property bool unknownVideo: (captures.video || []).length > 0
    readonly property bool active: enabled && (microphone || camera || screenSharing || unknownVideo || !captures.ready)

    Process {
        id: monitor
        command: ["python3", Quickshell.shellPath("scripts/privacy_monitor.py")]
        running: root.enabled
        stdout: SplitParser {
            onRead: data => {
                try { root.captures = JSON.parse(data); } catch (_) { root.captures = { ready: false }; }
            }
        }
        onExited: {
            root.captures = { ready: false };
            if (root.enabled) retry.restart();
        }
    }
    Timer { id: retry; interval: 3000; onTriggered: if (root.enabled) monitor.running = true }
    Timer { id: previewEnd; interval: 12000; onTriggered: root.preview = false }
    IpcHandler {
        target: "privacy"
        function status(): string {
            return JSON.stringify({ pipewire: root.captures, preview: root.preview,
                obs: ObsState.snapshot() });
        }
        // Prévia identificada e temporária; nunca substitui os dados reais.
        function previewIndicators(): void { root.preview = true; previewEnd.restart(); }
        function endPreview(): void { root.preview = false; previewEnd.stop(); }
    }
}
