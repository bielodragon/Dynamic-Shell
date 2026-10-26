pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Notifications
import qs.services

Singleton {
    id: root
    readonly property bool enabled: Preferences.enabled("notifications")
    onEnabledChanged: if (!enabled) { entries = []; previewItem = null; }
    property var entries: []
    property var previewItem: null
    readonly property bool doNotDisturb: !!ThemeStore.config.doNotDisturb
    readonly property var current: enabled ? previewItem || (entries.length ? entries[entries.length - 1] : null) : null
    readonly property int count: entries.length

    function setDoNotDisturb(enabled) { ThemeStore.setDoNotDisturb(enabled); }
    function toggleDoNotDisturb() { setDoNotDisturb(!doNotDisturb); }

    function remove(id) {
        entries = entries.filter(item => item.id !== id);
    }

    function dismissCurrent() {
        if (previewItem) { previewItem = null; return; }
        if (current) current.dismiss();
    }

    function expireCurrent() {
        if (previewItem) { previewItem = null; return; }
        if (current) current.expire();
    }

    function preview() {
        previewItem = {
            id: -1, appName: "Ilha", summary: "Notificação de teste",
            body: "A bolha sai da ilha e expande ao passar o mouse.",
            appIcon: "", actions: [], expireTimeout: 6
        };
    }

    LazyLoader {
      active: root.enabled
      NotificationServer {
        id: server
        bodySupported: true
        actionsSupported: true
        imageSupported: true
        keepOnReload: true
        onNotification: function(notification) {
            notification.tracked = true;
            root.remove(notification.id);
            notification.closed.connect(function() { root.remove(notification.id); });
            root.entries = root.entries.concat([notification]);
            if (root.entries.length > 20) root.entries[0].dismiss();
        }
    }
    }
}
