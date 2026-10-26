import QtQuick
import qs.services

Rectangle {
    id: root
    property string label: ""
    property bool emphasized: false
    signal clicked()

    implicitWidth: caption.implicitWidth + 24
    implicitHeight: 34
    radius: 10
    color: !enabled ? Theme.elevatedSurface : emphasized ? Theme.accent : Theme.elevatedSurface
    opacity: enabled ? 1 : 0.5

    Text {
        id: caption
        anchors.centerIn: parent
        text: root.label
        color: root.emphasized ? Theme.background : Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (root.enabled) root.clicked()
    }
}
