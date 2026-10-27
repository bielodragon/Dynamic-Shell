import Quickshell
import qs.modules
import qs.services

ShellRoot {
    readonly property bool themeLoaded: ThemeStore.ready
    readonly property bool shellReady: ShellState.islandVisible
    readonly property bool syncReady: ThemeSync.loaded
    readonly property bool deviceLoaded: DeviceState.showBattery
    readonly property bool appsLoaded: AppIntegrationsState.enabled
    Variants {
        model: Quickshell.screens
        delegate: LazyLoader {
            required property var modelData
            source: Quickshell.shellPath("modules/WallpaperSurface.qml")
            activeAsync: WallpaperState.enabled
            onActiveChanged: if (active && item) item.screen = modelData
        }
    }
    Variants {
        model: Quickshell.screens
        delegate: DeviceOverlay { required property var modelData; screen: modelData }
    }
    LazyLoader {
        activeAsync: SettingsState.opened
        SettingsWindow { }
    }
    Variants {
        model: Quickshell.screens
        delegate: ScreenCorners { required property var modelData; targetScreen: modelData }
    }
    Variants {
        model: Quickshell.screens

        // Cada monitor recebe uma superfície independente da ilha.
        delegate: Island {
            required property var modelData
            screen: modelData
        }
    }
    Variants {
        model: Quickshell.screens
        delegate: NotificationBubble {
            required property var modelData
            screen: modelData
        }
    }
}
