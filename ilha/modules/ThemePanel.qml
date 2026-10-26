import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.components
import qs.services

PanelWindow {
    id: root
    WlrLayershell.namespace: "ilha-themes"
    signal closeRequested()
    anchors.top: true
    margins.top: 78
    implicitWidth: Math.min(880, screen ? screen.width - 20 : 880)
    implicitHeight: Math.min(820, screen ? screen.height - 94 : 820)
    exclusiveZone: 0
    focusable: true
    color: Theme.transparent
    mask: Region { item: editor }
    ThemeEditor { id: editor; anchors.fill: parent; onCloseRequested: root.closeRequested() }
}
