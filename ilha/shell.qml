import Quickshell
import qs.modules
import qs.services

ShellRoot {
    readonly property bool themeLoaded: ThemeStore.ready
    readonly property bool shellReady: ShellState.islandVisible
    readonly property bool syncReady: ThemeSync.loaded
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
