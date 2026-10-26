pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property bool enabled: Preferences.enabled("phone")
    readonly property bool observerRunning: worker.running
    onEnabledChanged: { worker.running = enabled; if (!enabled) { devices = []; call = null; notice = null; previewItem = null; preview = false; } }
    property bool ready: false
    property bool nativeNotificationsOwned: false
    property var devices: []
    property string selectedId: ""
    property var notice: null
    property var call: null
    property bool preview: false
    property var previewItem: null
    readonly property var phones: devices.filter(device => device.paired && device.reachable
        && (device.type === "phone" || device.type === "tablet"))
    readonly property var phone: phones.find(device => device.id === selectedId) || phones[0] || null
    readonly property var current: enabled ? previewItem || call || notice : null

    function cycle() {
        if (phones.length > 1) selectedId = phones[(phones.indexOf(phone) + 1) % phones.length].id;
    }
    function dismiss() {
        if (previewItem) { previewItem = null; preview = false; }
        else if (call) call = null;
        else notice = null;
    }
    function receive(packet) {
        if (packet.kind === "snapshot") {
            ready = packet.ready;
            nativeNotificationsOwned = !!packet.nativeNotificationsOwned;
            devices = packet.devices;
            // Quando a Ilha é o servidor desktop, o KDE já entrega as bolhas por essa rota.
            // Usar somente uma rota evita repetir notificações e preserva ações nativas.
            if (nativeNotificationsOwned) { call = null; notice = null; }
            const reachable = devices.filter(device => device.paired && device.reachable).map(device => device.id);
            if (call && !reachable.includes(call.deviceId)) call = null;
            if (notice && !reachable.includes(notice.deviceId)) notice = null;
        } else if (packet.kind === "noticeRemoved") {
            if (notice && notice.deviceId === packet.deviceId && (!packet.id || notice.publicId === packet.id)) notice = null;
        } else if (!NotificationState.doNotDisturb && !nativeNotificationsOwned) {
            const device = devices.find(device => device.id === packet.deviceId);
            if (!device || !device.paired || !device.reachable) return;
            if (packet.kind === "call") {
                call = { deviceId: packet.deviceId, phoneSource: true,
                    appName: device.name, appIcon: "call-start", actions: [], expireTimeout: 25,
                    summary: (packet.event === "missedCall" ? "Chamada perdida: " : "Chamada recebida: ") + packet.contact,
                    body: "Atenda ou recuse no celular. Alerta temporário; o KDE Connect não informa o fim da chamada por esta interface.",
                    expiresAt: Date.now() + 25000 };
            } else if (packet.kind === "notice" && !packet.silent) {
                notice = { deviceId: packet.deviceId, publicId: packet.id, phoneSource: true,
                    appName: device.name + " · " + packet.appName, appIcon: "smartphone", actions: [],
                    summary: packet.title, body: packet.text, expireTimeout: 8, expiresAt: Date.now() + 8000 };
            }
        }
    }
    Process {
        id: worker
        command: ["python3", Quickshell.shellPath("scripts/kdeconnect_monitor.py")]
        running: root.enabled
        stdout: SplitParser { onRead: data => { try { root.receive(JSON.parse(data)); } catch (_) {} } }
        onExited: { root.ready = false; root.devices = []; root.call = null; root.notice = null; if (root.enabled) retry.restart(); }
    }
    Timer { id: retry; interval: 5000; onTriggered: if (root.enabled) worker.running = true }
    Timer {
        interval: 500; repeat: true; running: !!root.current
        onTriggered: {
            if (root.call && root.call.expiresAt <= Date.now()) root.call = null;
            if (root.notice && root.notice.expiresAt <= Date.now()) root.notice = null;
        }
    }
    Timer { id: previewEnd; interval: 12000; onTriggered: { root.preview = false; root.previewItem = null; } }
    IpcHandler {
        target: "phone"
        function status(): string {
            return JSON.stringify({ ready: root.ready, devices: root.devices, preview: root.preview,
                nativeNotificationsOwned: root.nativeNotificationsOwned,
                hasCallAlert: !!root.call, hasNotification: !!root.notice });
        }
        function previewCall(): void {
            root.preview = true;
            root.previewItem = { phoneSource: true, appName: "Prévia · Celular", appIcon: "call-start", actions: [],
                summary: "Chamada recebida: Contato de teste", body: "Prévia visual. Atenda ou recuse chamadas reais no celular.",
                expireTimeout: 12, expiresAt: Date.now() + 12000 };
            previewEnd.restart();
        }
        function endPreview(): void {
            root.previewItem = null;
            root.preview = false; previewEnd.stop();
        }
    }
}
