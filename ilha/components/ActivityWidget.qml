import QtQuick
import qs.services

Item {
    id: root
    required property bool expanded
    readonly property var activity: ActivityState.current
    readonly property color statusColor: !activity ? Theme.accent
        : activity.state === "success" ? Theme.success
        : activity.state === "error" ? Theme.error
        : activity.state === "waiting" ? Theme.warning : Theme.accent
    readonly property string statusLabel: !activity ? ""
        : ({ running: "Trabalhando", waiting: "Aguardando você", paused: "Pausado",
             success: "Concluído", error: "Erro" })[activity.state]
    width: expanded ? 225 : 132
    height: expanded ? 49 : 25
    Behavior on width { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }

    Rectangle {
        x: 0; y: root.expanded ? 6 : 4
        width: 7; height: 7; radius: 3.5
        color: root.statusColor
    }
    Text {
        x: 14; y: 0
        width: root.width - 42
        text: root.activity ? root.activity.title : ""
        color: Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: root.expanded ? 12 : 10
        font.weight: Font.DemiBold
        elide: Text.ElideRight
        textFormat: Text.PlainText
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: ActivityState.cycle()
        }
    }
    Text {
        x: 14; y: 19
        width: root.width - 28
        visible: root.expanded
        text: root.activity ? root.statusLabel
            + (root.activity.progress !== null ? " · " + Math.round(root.activity.progress) + "%" : "")
            + " · " + (root.activity.detail || root.activity.app) : ""
        color: Theme.secondaryText
        font.family: Theme.fontFamily
        font.pixelSize: 10
        elide: Text.ElideRight
        textFormat: Text.PlainText
    }
    Text {
        anchors.right: parent.right
        text: ActivityState.entries.length > 1 ? "+" + (ActivityState.entries.length - 1) : "×"
        color: Theme.secondaryText
        font.family: Theme.fontFamily
        font.pixelSize: 12
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                if (ActivityState.entries.length > 1) ActivityState.cycle();
                else if (root.activity) ActivityState.remove(root.activity.id);
            }
        }
    }
    Rectangle {
        id: track
        x: 14; y: root.expanded ? 42 : 21
        width: root.width - 28
        height: 3; radius: 1.5
        clip: true
        color: Theme.elevatedSurface
        Rectangle {
            id: progress
            readonly property bool indeterminate: root.activity && root.activity.progress === null
                && root.activity.state === "running"
            x: 0
            width: indeterminate ? track.width * 0.3
                : root.activity && root.activity.progress !== null ? track.width * root.activity.progress / 100 : 0
            height: 3; radius: 1.5
            color: root.statusColor
            Behavior on width { NumberAnimation { duration: Theme.contentDuration } }
            NumberAnimation on x {
                from: -progress.width
                to: track.width
                duration: 1500 * Math.max(0.5, Preferences.animationScale)
                loops: Animation.Infinite
                running: Preferences.animationsEnabled && progress.indeterminate && root.visible
            }
            onIndeterminateChanged: if (!indeterminate) x = 0
        }
    }
}
