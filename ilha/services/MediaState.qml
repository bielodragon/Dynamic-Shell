pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Services.Mpris

Singleton {
    id: root
    readonly property var players: Mpris.players.values
    readonly property var playingPlayer: Preferences.enabled("media") ? players.find(player => player.isPlaying && player.trackTitle)
        || players.find(player => player.isPlaying) || null : null
    property var lastPlayer: null
    readonly property var focusedWindow: Hyprland.toplevels.values.find(window => window.activated) || null
    readonly property var visiblePlayer: Preferences.enabled("media") && lastPlayer && players.includes(lastPlayer)
        && !isForeground(lastPlayer, focusedWindow) ? lastPlayer : null

    function isForeground(player, window) {
        if (!player || !window) return false;
        const ipc = window.lastIpcObject || {};
        const appClass = String(ipc.class || ipc.initialClass || "").toLowerCase();
        const entry = String(player.desktopEntry || player.identity || "").toLowerCase();
        return appClass.length > 0 && entry.length > 0
            && (appClass === entry || appClass.includes(entry) || entry.includes(appClass));
    }

    function toggle() {
        if (visiblePlayer && visiblePlayer.canTogglePlaying) visiblePlayer.togglePlaying();
    }
    function next() {
        if (visiblePlayer && visiblePlayer.canGoNext) visiblePlayer.next();
    }
    function previous() {
        if (visiblePlayer && visiblePlayer.canGoPrevious) visiblePlayer.previous();
    }

    onPlayingPlayerChanged: {
        if (playingPlayer) {
            lastPlayer = playingPlayer;
            pauseGrace.stop();
        } else if (lastPlayer) pauseGrace.restart();
    }
    onPlayersChanged: {
        if (lastPlayer && !players.includes(lastPlayer)) lastPlayer = null;
    }

    // Depois de pausar, mantém os controles por alguns segundos para retomar.
    Timer {
        id: pauseGrace
        interval: 20000
        onTriggered: if (!root.playingPlayer) root.lastPlayer = null
    }
}
