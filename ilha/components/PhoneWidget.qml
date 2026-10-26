import QtQuick
import qs.services

Row {
    id: root
    property bool expanded: false
    readonly property var phone: KdeConnectState.phone
    visible: !!phone
    spacing: 6
    height: 24
    Text {
        anchors.verticalCenter: parent.verticalCenter
        text: "󰄜"
        font.family: Theme.fontFamily; font.pixelSize: 16
        color: root.phone && root.phone.charge !== null && root.phone.charge <= 15 ? Theme.warning : Theme.accent
    }
    Text {
        anchors.verticalCenter: parent.verticalCenter
        text: root.phone ? (root.phone.charge === null ? "—" : root.phone.charge + "%")
            + (root.phone.charging ? " ⚡" : "") : ""
        font.family: Theme.fontFamily; font.pixelSize: 11
        color: Theme.text
    }
    Text {
        visible: root.expanded
        anchors.verticalCenter: parent.verticalCenter
        text: root.phone ? root.phone.name + (KdeConnectState.phones.length > 1 ? " +" + (KdeConnectState.phones.length - 1) : "") : ""
        width: Math.min(100, implicitWidth)
        elide: Text.ElideRight
        textFormat: Text.PlainText
        font.family: Theme.fontFamily; font.pixelSize: 10
        color: Theme.secondaryText
        MouseArea { anchors.fill: parent; onClicked: KdeConnectState.cycle() }
    }
}
