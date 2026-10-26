pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "../components/ActivityModel.js" as Model

Singleton {
    id: root
    readonly property bool enabled: Preferences.enabled("activities")
    onEnabledChanged: if (!enabled) entries = []
    property var entries: []
    property string selectedId: ""
    readonly property var current: entries.find(item => item.id === selectedId) || entries[0] || null

    function update(payload) {
        if (!enabled) throw new Error("Módulo de atividades desativado.");
        entries = Model.apply(Model.prune(entries, Date.now()), payload, Date.now());
    }
    function remove(id) {
        entries = entries.filter(item => item.id !== id);
    }
    function cycle() {
        if (entries.length < 2 || !current) return;
        selectedId = entries[(entries.indexOf(current) + 1) % entries.length].id;
    }

    IpcHandler {
        target: "activities"
        function update(payload: string): string {
            try {
                if (payload.length > 4096) throw new Error("Atividade maior que 4 KiB.");
                root.update(JSON.parse(payload));
                return JSON.stringify({ ok: true });
            } catch (error) {
                return JSON.stringify({ ok: false, error: String(error.message || error) });
            }
        }
        function remove(id: string): string {
            root.remove(id);
            return JSON.stringify({ ok: true });
        }
        function list(): string { return JSON.stringify({ ok: true, activities: root.entries }); }
    }
    Timer {
        interval: 1000
        repeat: true
        running: root.entries.length > 0
        onTriggered: {
            const fresh = Model.prune(root.entries, Date.now());
            if (fresh.length !== root.entries.length) root.entries = fresh;
        }
    }
}
