import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import qs.components
import qs.services
import qs.modules

PanelWindow {
    id: panel
    WlrLayershell.namespace: "ilha-island"
    anchors.top: true
    margins.top: ThemeStore.config.island ? ThemeStore.config.island.topMargin : 8
    implicitWidth: Math.max(450, island.width + 16)
    implicitHeight: 96
    exclusiveZone: 0
    color: Theme.transparent
    focusable: false
    mask: Region { item: island; Region { item: pullHandle; intersection: Intersection.Combine } }
    property bool themePanelOpen: false
    readonly property bool launcherHere: LauncherState.present && LauncherState.screenName === (screen ? screen.name : "")
    visible: ShellState.islandVisible && !launcherHere
    Connections {
        target: ShellState
        function onIslandVisibleChanged() { if (!ShellState.islandVisible) panel.themePanelOpen = false; }
    }
    function openLauncher() {
        themePanelOpen = false;
        LauncherState.open(screen ? screen.name : "", island.width, island.height, island.radius);
    }
    Connections {
        target: LauncherState
        function onOpenedChanged() {
            if (!LauncherState.opened && panel.launcherHere) {
                // Fechar na geometria atual da ilha evita pular de hover para repouso.
                LauncherState.originWidth = island.width;
                LauncherState.originHeight = island.height;
                LauncherState.originRadius = island.radius;
            }
        }
    }
    // Atividades futuras podem solicitar o formato compacto sem remover workspaces.
    readonly property bool activityPresent: activityTitle.length > 0
        || (NotificationState.current && !NotificationState.doNotDisturb)
        || !!MediaState.visiblePlayer
        || !!ActivityState.current
        || PrivacyState.active || ObsState.recording
        || !!KdeConnectState.current
    property string activityTitle: ""
    function openControls() {
        themePanelOpen = false;
        ControlCenterState.open(screen ? screen.name : "");
    }

    IpcHandler {
        target: panel.screen ? "ilha." + panel.screen.name : "ilha"
        function toggleThemes(): void { panel.themePanelOpen = !panel.themePanelOpen; }
        function setTheme(themeId: string): void { ThemeStore.select(themeId); }
        function getTheme(): string { return ThemeStore.config.theme; }
        function setWorkspaceStyle(style: string): void { ThemeStore.setWorkspaceStyle(style); }
        function getWorkspaceStyle(): string { return ThemeStore.config.workspaceStyle || "icons"; }
        function showActivity(title: string): void {
            panel.activityTitle = title;
        }
        function hideActivity(): void { panel.activityTitle = ""; }
        function nextWorkspace(): void { workspaceDots.step(1); }
        function previousWorkspace(): void { workspaceDots.step(-1); }
        function previewNotification(): void { NotificationState.preview(); }
        function dismissNotification(): void { NotificationState.dismissCurrent(); }
        function setDoNotDisturb(enabled: bool): void { NotificationState.setDoNotDisturb(enabled); }
        function toggleDoNotDisturb(): void { NotificationState.toggleDoNotDisturb(); }
        function getDoNotDisturb(): bool { return NotificationState.doNotDisturb; }
        function getMedia(): string { return MediaState.visiblePlayer ? MediaState.visiblePlayer.trackTitle : ""; }
        function toggleMedia(): void { MediaState.toggle(); }
        function nextMedia(): void { MediaState.next(); }
        function previousMedia(): void { MediaState.previous(); }
        function openControls(): void { panel.openControls(); }
        function openLauncher(): void { panel.openLauncher(); }
    }

    LazyLoader {
        activeAsync: panel.themePanelOpen
        ThemePanel {
            screen: panel.screen
            onCloseRequested: panel.themePanelOpen = false
        }
    }
    LazyLoader {
        id: controlLoader
        property bool keepAlive: false
        activeAsync: keepAlive || (ControlCenterState.opened && ControlCenterState.screenName === (panel.screen ? panel.screen.name : ""))
        ControlCenter {
            screen: panel.screen
            Component.onCompleted: controlLoader.keepAlive = true
            onFinished: controlLoader.keepAlive = false
            onThemesRequested: panel.themePanelOpen = true
        }
    }
    LazyLoader {
        id: launcherLoader
        property bool keepAlive: false
        activeAsync: keepAlive || (LauncherState.opened && LauncherState.screenName === (panel.screen ? panel.screen.name : ""))
        LauncherWindow {
            screen: panel.screen
            Component.onCompleted: launcherLoader.keepAlive = true
            onFinished: { launcherLoader.keepAlive = false; LauncherState.finishClose(); }
        }
    }

    Rectangle {
        id: pullHandle
        anchors.horizontalCenter: island.horizontalCenter
        anchors.top: island.bottom; anchors.topMargin: 4
        width: 44; height: 12; radius: 6
        color: Theme.transparent
        Rectangle { anchors.centerIn: parent; width: 28; height: 3; radius: 2; color: Theme.secondaryText; opacity: 0.65 }
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            property real startY: 0
            onPressed: mouse => startY = mouse.y
            onReleased: mouse => { if (mouse.y - startY > 18) panel.openControls(); }
            onClicked: panel.openControls()
        }
    }

    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }

    Rectangle {
        id: island
        property string mode: "idle"
        readonly property bool expanded: mode === "expanded"
        property string pulseName: ""

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        width: Math.max(mode === "expanded" ? 300 : mode === "compact" ? 212 : 174,
                        contentRow.width + (mode === "expanded" ? 54 : 36))
        height: mode === "expanded" ? 66 : mode === "compact" ? 42 : 36
        radius: mode === "expanded" ? 25 : height / 2
        color: Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, Theme.effectiveGlassOpacity)
        border.color: Theme.border
        border.width: 1

        Behavior on width {
            enabled: Preferences.animationsEnabled
            SpringAnimation { spring: 4 / Math.pow(Math.max(0.5, Preferences.animationScale), 2); damping: 0.45; epsilon: 0.15 }
        }
        Behavior on height {
            enabled: Preferences.animationsEnabled
            SpringAnimation { spring: 4 / Math.pow(Math.max(0.5, Preferences.animationScale), 2); damping: 0.45; epsilon: 0.15 }
        }
        Behavior on radius {
            NumberAnimation { duration: Theme.morphDuration; easing.type: Easing.OutCubic }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property real startY: 0
            property bool pulled: false
            onPressed: mouse => { startY = mouse.y; pulled = false; }
            onPositionChanged: mouse => {
                if (pressed && mouse.y - startY > 24 && !pulled) { pulled = true; panel.openControls(); }
            }
            onClicked: mouse => { if (!pulled) { if (mouse.button === Qt.RightButton) panel.openLauncher(); else panel.themePanelOpen = !panel.themePanelOpen; } }
        }

        HoverHandler {
            onHoveredChanged: {
                if (hovered) {
                    island.mode = "compact";
                    expandDelay.restart();
                } else {
                    expandDelay.stop();
                    island.mode = "idle";
                }
            }
        }
        WheelHandler {
            enabled: Preferences.enabled("workspaces")
            onWheel: function(event) {
                workspaceDots.step(event.angleDelta.y > 0 ? -1 : 1);
                event.accepted = true;
            }
        }

        Row {
            id: contentRow
            anchors.centerIn: parent
            spacing: island.expanded ? 20 : 12

            Behavior on spacing {
                NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic }
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: Preferences.enabled("clock")
                text: Qt.formatDateTime(clock.date, "HH:mm")
                color: Theme.text
                font.family: Theme.fontFamily
                font.pixelSize: island.expanded ? 20 : 14
                font.weight: Font.DemiBold

                Behavior on font.pixelSize {
                    NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic }
                }
            }

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 1
                height: island.expanded ? 26 : 14
                visible: Preferences.enabled("clock") && (Preferences.enabled("workspaces") || panel.activityPresent || !!KdeConnectState.phone)
                color: Theme.border
            }

            WorkspaceDots {
                id: workspaceDots
                visible: Preferences.enabled("workspaces")
                anchors.verticalCenter: parent.verticalCenter
                targetScreen: panel.screen
                expanded: island.expanded
                activityCompact: panel.activityPresent
                style: ThemeStore.config.workspaceStyle || "icons"
                maxVisible: PrivacyState.active || ObsState.recording || (ActivityState.current && MediaState.visiblePlayer) ? 3
                    : ThemeStore.config.maxVisibleWorkspaces || 6
                onWorkspaceActivated: function(name) {
                    island.pulseName = name;
                    pulseTimer.restart();
                }
            }
            MediaWidget {
                anchors.verticalCenter: parent.verticalCenter
                visible: !!MediaState.visiblePlayer
                player: MediaState.visiblePlayer
                expanded: island.expanded && !ActivityState.current && !PrivacyState.active && !ObsState.recording
                onExpandRequested: island.mode = "expanded"
            }
            ActivityWidget {
                anchors.verticalCenter: parent.verticalCenter
                visible: !!ActivityState.current
                expanded: island.expanded && !PrivacyState.active && !ObsState.recording
            }
            PrivacyWidget {
                anchors.verticalCenter: parent.verticalCenter
                expanded: island.expanded
            }
            PhoneWidget {
                anchors.verticalCenter: parent.verticalCenter
                expanded: island.expanded && !PrivacyState.active && !ActivityState.current && !MediaState.visiblePlayer
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: panel.activityTitle.length > 0
                    || (!MediaState.visiblePlayer && NotificationState.current && !NotificationState.doNotDisturb)
                    || pulseTimer.running
                text: panel.activityTitle.length > 0 ? panel.activityTitle
                    : NotificationState.current && !NotificationState.doNotDisturb ? "Notificação" : island.pulseName
                color: Theme.text
                font.family: Theme.fontFamily
                font.pixelSize: island.expanded ? 12 : 10
                elide: Text.ElideRight
                width: visible ? Math.min(110, implicitWidth) : 0
            }
        }

        Timer { id: pulseTimer; interval: 850 }
        Timer {
            id: expandDelay
            interval: ThemeStore.config.island ? ThemeStore.config.island.hoverExpandDelayMs : 170
            onTriggered: island.mode = "expanded"
        }

    }
}
