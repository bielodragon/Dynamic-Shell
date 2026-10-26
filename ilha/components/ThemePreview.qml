import QtQuick
import qs.services

Row {
    spacing: 12

    Column {
        spacing: 5
        Rectangle {
            width: 120; height: 38; radius: 18
            color: Theme.surface
            border.color: Theme.border
            Text { anchors.centerIn: parent; text: "15:08   ● ●"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
        }
        Text { text: "Ilha"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10 }
    }

    Column {
        spacing: 5
        Rectangle {
            width: 120; height: 38; radius: 10
            color: Theme.elevatedSurface
            border.color: Theme.border
            Rectangle { x: 9; y: 8; width: 36; height: 22; radius: 7; color: Theme.accent }
            Text { x: 52; anchors.verticalCenter: parent.verticalCenter; text: "Wi-Fi"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
        }
        Text { text: "Control Center"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10 }
    }

    Column {
        spacing: 5
        Rectangle {
            width: 120; height: 38; radius: 18
            color: Theme.surface
            border.color: Theme.border
            Rectangle { x: 9; anchors.verticalCenter: parent.verticalCenter; width: 7; height: 7; radius: 4; color: Theme.success }
            Text { x: 22; anchors.verticalCenter: parent.verticalCenter; text: "Atividade"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
        }
        Text { text: "Bolha"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10 }
    }
}
