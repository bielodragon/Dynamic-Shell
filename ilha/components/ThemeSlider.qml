import QtQuick
import QtQuick.Controls
import qs.services

Slider {
    implicitHeight: 28
    background: Rectangle {
        x: 0
        y: 11
        width: parent.width
        height: 6
        radius: 3
        color: Theme.elevatedSurface
        Rectangle {
            width: parent.parent.visualPosition * parent.width
            height: parent.height
            radius: parent.radius
            color: Theme.accent
        }
    }
    handle: Rectangle {
        x: parent.visualPosition * (parent.width - width)
        y: 4
        width: 19
        height: 19
        radius: 10
        color: Theme.accent
        border.color: Theme.border
    }
}
