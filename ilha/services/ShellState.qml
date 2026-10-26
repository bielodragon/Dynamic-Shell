pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property bool islandVisible: !ThemeStore.config.shell || ThemeStore.config.shell.islandVisible !== false
    function setIslandVisible(value) {
        LauncherState.close(); ControlCenterState.close();
        ThemeStore.setPreferences({shell:{islandVisible:value}});
    }
    IpcHandler {
        target: "shell"
        function toggleIsland(): void { root.setIslandVisible(!root.islandVisible); }
        function showIsland(): void { root.setIslandVisible(true); }
        function hideIsland(): void { root.setIslandVisible(false); }
        function status(): string { return JSON.stringify({running:true,islandVisible:root.islandVisible,ready:ThemeStore.ready}); }
    }
}
