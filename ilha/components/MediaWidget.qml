import QtQuick
import Quickshell
import Quickshell.Widgets
import qs.services

Item {
    id: root
    required property var player
    required property bool expanded
    signal expandRequested()
    width: expanded ? 245 : 73
    height: expanded ? 54 : 30
    Behavior on width { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }

    Rectangle {
        id: cover
        x: 0
        anchors.verticalCenter: parent.verticalCenter
        width: root.expanded ? 43 : 28
        height: width
        radius: root.expanded ? 9 : 7
        color: Theme.elevatedSurface
        clip: true
        Image {
            id: artwork
            anchors.fill: parent
            source: root.player ? root.player.trackArtUrl : ""
            sourceSize.width: 96
            sourceSize.height: 96
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            visible: status === Image.Ready
        }
        IconImage {
            anchors.centerIn: parent
            width: root.expanded ? 23 : 17
            height: width
            visible: !artwork.visible && source !== ""
            source: root.player && root.player.desktopEntry
                ? Quickshell.iconPath(root.player.desktopEntry, true) : ""
        }
        Text {
            anchors.centerIn: parent
            visible: !artwork.visible && root.player && !root.player.desktopEntry
            text: "♪"
            color: Theme.accent
            font.family: Theme.fontFamily
            font.pixelSize: 18
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.expandRequested()
        }
    }

    Row {
        x: 37
        anchors.verticalCenter: parent.verticalCenter
        spacing: 3
        visible: !root.expanded
        Repeater {
            model: 3
            Rectangle {
                id: bar
                required property int index
                width: 4
                height: 7 + index * 3
                radius: 2
                color: Theme.accent
                opacity: root.player && root.player.isPlaying ? 0.95 : 0.45
                SequentialAnimation on height {
                    running: Preferences.animationsEnabled && root.player && root.player.isPlaying && !root.expanded
                    loops: Animation.Infinite
                    NumberAnimation { to: 17 - bar.index * 3; duration: (320 + bar.index * 70) * Math.max(0.5, Preferences.animationScale); easing.type: Easing.InOutSine }
                    NumberAnimation { to: 6 + bar.index * 2; duration: (390 + bar.index * 90) * Math.max(0.5, Preferences.animationScale); easing.type: Easing.InOutSine }
                }
            }
        }
    }

    Text {
        x: 52; y: 0
        width: root.width - 54
        visible: root.expanded
        text: root.player ? (root.player.trackTitle || root.player.identity) : ""
        color: Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: 11
        font.weight: Font.DemiBold
        elide: Text.ElideRight
        textFormat: Text.PlainText
    }
    Text {
        x: 52; y: 16
        width: root.width - 54
        visible: root.expanded
        text: root.player ? (root.player.trackArtist || root.player.identity) : ""
        color: Theme.secondaryText
        font.family: Theme.fontFamily
        font.pixelSize: 10
        elide: Text.ElideRight
        textFormat: Text.PlainText
    }
    Row {
        x: 52; y: 32
        visible: root.expanded && root.player
        spacing: 6
        Repeater {
            model: [
                { symbol: "‹", enabled: root.player && root.player.canGoPrevious, action: "previous" },
                { symbol: root.player && root.player.isPlaying ? "Ⅱ" : "▶",
                  enabled: root.player && root.player.canTogglePlaying, action: "toggle" },
                { symbol: "›", enabled: root.player && root.player.canGoNext, action: "next" }
            ]
            Rectangle {
                id: button
                required property var modelData
                width: 27; height: 21; radius: 10
                color: Theme.elevatedSurface
                opacity: modelData.enabled ? 1 : 0.35
                Text {
                    anchors.centerIn: parent
                    text: button.modelData.symbol
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                }
                MouseArea {
                    anchors.fill: parent
                    enabled: button.modelData.enabled
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (!root.player) return;
                        if (button.modelData.action === "toggle") root.player.togglePlaying();
                        else if (button.modelData.action === "next") root.player.next();
                        else root.player.previous();
                    }
                }
            }
        }
    }
}
