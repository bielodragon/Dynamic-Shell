import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Widgets
import qs.services

PanelWindow {
    id: panel
    WlrLayershell.namespace: "ilha-notifications"
    anchors.top: true
    anchors.right: true
    margins.top: 18
    margins.right: screen ? Math.max(12, screen.width / 2 - 645) : 12
    implicitWidth: 348
    implicitHeight: expanded ? 156 : 56
    exclusiveZone: 0
    color: Theme.transparent
    mask: Region { item: bubble }
    property bool expanded: false
    readonly property var current: KdeConnectState.current || NotificationState.current
    readonly property bool onFocusedScreen: screen && Hyprland.focusedMonitor
        && Hyprland.focusedMonitor.name === screen.name
    visible: !!current && !NotificationState.doNotDisturb && onFocusedScreen

    onCurrentChanged: {
        expanded = false;
        if (current && !NotificationState.doNotDisturb) autoExpire.restart();
        else autoExpire.stop();
    }
    onVisibleChanged: if (visible && current) autoExpire.restart()

    Timer {
        id: autoExpire
        interval: panel.current && panel.current.expireTimeout > 0
            ? Math.max(3000, panel.current.expireTimeout * 1000) : 6000
        onTriggered: panel.current && panel.current.phoneSource ? KdeConnectState.dismiss() : NotificationState.expireCurrent()
    }

    Rectangle {
        id: bubble
        anchors.fill: parent
        radius: panel.expanded ? 22 : 28
        color: Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, Theme.effectiveGlassOpacity)
        border.color: Theme.border
        border.width: 1
        Behavior on radius { NumberAnimation { duration: Theme.morphDuration; easing.type: Easing.OutCubic } }

        HoverHandler {
            onHoveredChanged: {
                panel.expanded = hovered;
                if (hovered) autoExpire.stop();
                else if (panel.current) autoExpire.restart();
            }
        }

        IconImage {
            id: icon
            x: 14; y: 14; width: 28; height: 28
            source: panel.current && panel.current.appIcon
                ? Quickshell.iconPath(panel.current.appIcon, true) : ""
            visible: source !== ""
        }
        Rectangle {
            x: 14; y: 14; width: 28; height: 28; radius: 14
            color: Theme.accent
            visible: !icon.visible
            Text {
                anchors.centerIn: parent
                text: "●"
                color: Theme.background
                font.family: Theme.fontFamily
                font.pixelSize: 14
            }
        }
        Text {
            x: 51; y: panel.expanded ? 17 : 11
            width: bubble.width - 91
            text: panel.current ? (panel.expanded ? panel.current.appName : panel.current.summary) : ""
            color: Theme.text
            font.family: Theme.fontFamily
            font.pixelSize: panel.expanded ? 10 : 12
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            textFormat: Text.PlainText
        }
        Text {
            x: 51; y: 35; width: bubble.width - 91
            visible: panel.expanded
            text: panel.current ? panel.current.summary : ""
            color: Theme.text
            font.family: Theme.fontFamily
            font.pixelSize: 13
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            textFormat: Text.PlainText
        }
        Text {
            x: 17; y: 65
            width: bubble.width - 34
            height: 47
            visible: panel.expanded
            text: panel.current ? panel.current.body : ""
            color: Theme.secondaryText
            font.family: Theme.fontFamily
            font.pixelSize: 11
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            textFormat: Text.PlainText
        }
        Row {
            x: 17; y: 120
            visible: panel.expanded && panel.current
            spacing: 8
            Repeater {
                model: panel.current ? Array.from(panel.current.actions).slice(0, 2) : []
                Rectangle {
                    id: actionButton
                    required property var modelData
                    width: Math.min(115, label.implicitWidth + 20)
                    height: 25; radius: 12
                    color: Theme.elevatedSurface
                    Text {
                        id: label
                        anchors.centerIn: parent
                        text: actionButton.modelData.text
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }
                    MouseArea { anchors.fill: parent; onClicked: actionButton.modelData.invoke() }
                }
            }
        }
        Text {
            anchors.right: parent.right
            anchors.rightMargin: 14
            y: panel.expanded ? 14 : 17
            text: "×"
            color: Theme.secondaryText
            font.family: Theme.fontFamily
            font.pixelSize: 17
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: panel.current && panel.current.phoneSource ? KdeConnectState.dismiss() : NotificationState.dismissCurrent()
            }
        }
    }
    Behavior on implicitHeight {
        NumberAnimation { duration: Theme.morphDuration; easing.type: Easing.OutCubic }
    }
}
