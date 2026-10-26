import QtQuick
import qs.services

Row {
    id: root
    property bool expanded: false
    function timecode() {
        const seconds = Math.floor(ObsState.duration / 1000);
        return (seconds >= 3600 ? Math.floor(seconds / 3600) + ":" : "")
            + String(Math.floor(seconds / 60) % 60).padStart(2, "0")
            + ":" + String(seconds % 60).padStart(2, "0");
    }
    spacing: expanded ? 10 : 6
    visible: !!PrivacyState.enabled && (PrivacyState.active || ObsState.recording)
    height: 26
    Repeater {
        model: [
            { shown: PrivacyState.microphone, label: "Mic", token: Theme.warning },
            { shown: PrivacyState.camera, label: "Câmera", token: Theme.success },
            { shown: PrivacyState.screenSharing, label: "Tela", token: Theme.accent },
            { shown: PrivacyState.unknownVideo, label: "Vídeo", token: Theme.warning },
            { shown: !PrivacyState.captures.ready, label: "PipeWire indisponível", token: Theme.error }
        ]
        delegate: Row {
            required property var modelData
            anchors.verticalCenter: parent.verticalCenter
            visible: modelData.shown
            spacing: 5
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 7; height: 7; radius: 3.5
                color: modelData.token
                Behavior on color { ColorAnimation { duration: Theme.contentDuration } }
            }
            Text {
                visible: root.expanded
                text: modelData.label
                font.family: Theme.fontFamily; font.pixelSize: 10
                color: Theme.secondaryText
            }
        }
    }
    Text {
        anchors.verticalCenter: parent.verticalCenter
        visible: PrivacyState.preview
        text: "Prévia"
        color: Theme.secondaryText
        font.family: Theme.fontFamily; font.pixelSize: 10
    }
    Rectangle {
        visible: ObsState.recording
        anchors.verticalCenter: parent.verticalCenter
        width: recordRow.width + 16; height: 26; radius: 13
        color: Theme.elevatedSurface
        border.color: Theme.border
        Row {
            id: recordRow
            anchors.centerIn: parent
            spacing: 6
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 7; height: 7; radius: 3.5
                color: ObsState.paused ? Theme.warning : Theme.error
            }
            Text {
                text: (ObsState.paused ? "Pausa " : root.expanded ? "Gravando " : "") + root.timecode()
                color: Theme.text
                font.family: Theme.fontFamily; font.pixelSize: 11
            }
        }
    }
}
