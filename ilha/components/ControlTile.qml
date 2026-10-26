import QtQuick
import QtQuick.Controls
import qs.services

Rectangle {
    id: root
    property string title: ""
    property string detail: ""
    property string symbol: ""
    property bool active: false
    signal clicked()
    implicitWidth: 240; implicitHeight: 72
    radius: 18
    color: active ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.17) : Theme.elevatedSurface
    border.color: active ? Theme.accent : Theme.border
    opacity: enabled ? 1 : 0.5
    Behavior on color { ColorAnimation { duration: Theme.contentDuration } }
    Text {
        x: 14; anchors.verticalCenter: parent.verticalCenter
        text: root.symbol
        color: root.active ? Theme.accent : Theme.secondaryText
        font.family: Theme.fontFamily; font.pixelSize: 23
    }
    Text {
        x: 52; y: 15; width: parent.width - 64
        text: root.title
        color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 12
        textFormat: Text.PlainText; elide: Text.ElideRight
    }
    Text {
        x: 52; y: 38; width: parent.width - 64
        text: root.detail
        color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10
        textFormat: Text.PlainText; elide: Text.ElideRight
    }
    MouseArea {
        id: mouse
        anchors.fill: parent; hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
    ToolTip {
        visible: mouse.containsMouse && root.detail.length > 0
        delay: 700
        text: root.detail
        contentItem: Text { text: root.detail; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
        background: Rectangle { color: Theme.elevatedSurface; border.color: Theme.border; radius: 8 }
    }
}
