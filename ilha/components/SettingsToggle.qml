import QtQuick
import qs.services

Rectangle {
    id: root
    property string label: ""
    property string description: ""
    property bool checked: false
    signal toggled()
    width: parent ? parent.width : 400
    height: 66; radius: 14
    color: Theme.elevatedSurface
    border.color: activeFocus ? Theme.accent : Theme.border
    activeFocusOnTab: true
    Keys.onSpacePressed: toggled()
    Keys.onReturnPressed: toggled()
    Text { x: 16; y: 12; width: parent.width - 92; text: root.label; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13 }
    Text { x: 16; y: 36; width: parent.width - 92; text: root.description; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10; elide: Text.ElideRight; textFormat: Text.PlainText }
    Rectangle {
        anchors.right: parent.right; anchors.rightMargin: 16; anchors.verticalCenter: parent.verticalCenter
        width: 42; height: 24; radius: 12; color: root.checked ? Theme.accent : Theme.border
        Rectangle { x: root.checked ? 21 : 3; y: 3; width: 18; height: 18; radius: 9; color: root.checked ? Theme.background : Theme.text
            Behavior on x { NumberAnimation { duration: Theme.contentDuration } }
        }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.toggled() }
}
