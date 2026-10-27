import QtQuick
import qs.services

Text {
    visible: DeviceState.showBattery && DeviceState.batteries.length > 0
    text: DeviceState.batteries.map(b => (b.status === "Charging" ? "󰂄 " : "󰁹 ") + b.percent + "%").join(" · ")
    color: DeviceState.batteries.some(b => b.percent <= 20 && b.status === "Discharging") ? Theme.warning : Theme.text
    font.family: Theme.fontFamily; font.pixelSize: 12
}
