import QtQuick
import qs.services

Rectangle {
    id: root
    required property var themeData
    signal chosen()
    width: 140; height: 82; radius: 14
    color: themeData.colors.surface
    border.width: ThemeStore.config.theme === themeData.id ? 2 : 1
    border.color: ThemeStore.config.theme === themeData.id ? Theme.accent : themeData.colors.border
    Rectangle {
        x: 12; y: 12; width: 70; height: 19; radius: 10
        color: root.themeData.colors.background
        Rectangle { x: 44; y: 6; width: 16; height: 6; radius: 3; color: root.themeData.colors.accent }
    }
    Row {
        x: 12; y: 39; spacing: 5
        Repeater {
            model: ["accent", "text", "success", "warning", "error"]
            Rectangle { required property string modelData; width: 12; height: 8; radius: 4; color: root.themeData.colors[modelData] }
        }
    }
    Text {
        x: 12; y: 57; width: parent.width - 24
        text: root.themeData.name; textFormat: Text.PlainText; elide: Text.ElideRight
        color: root.themeData.colors.text; font.family: Theme.fontFamily; font.pixelSize: 10
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.chosen() }
}
