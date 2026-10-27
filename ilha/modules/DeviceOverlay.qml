import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services

PanelWindow {
    WlrLayershell.namespace: "ilha-device-status"
    anchors.top: true; anchors.right: true
    margins.top: (NotificationState.current || KdeConnectState.current) && !NotificationState.doNotDisturb ? 188 : 12
    margins.right: 12
    exclusionMode: ExclusionMode.Ignore
    implicitWidth: 255; implicitHeight: lines.implicitHeight + 24
    color: Theme.transparent
    visible: DeviceState.showMetrics
    mask: Region {}
    Rectangle {
        anchors.fill: parent; radius: 14
        color: Qt.rgba(Theme.surface.r,Theme.surface.g,Theme.surface.b,Theme.effectiveGlassOpacity)
        border.color: Theme.border
        Text {
            id: lines
            x: 12; y: 12
            text: {
                const d=DeviceState.data, t=d.temperature || {}, mem=d.memory || {};
                const rows=["Status do dispositivo",
                    "CPU " + (d.cpu === undefined || d.cpu === null ? "—" : d.cpu + "%") + (t.cpu === null || t.cpu === undefined ? "" : " · " + Math.round(t.cpu) + "°C"),
                    "RAM " + (mem.percent === undefined ? "—" : mem.percent + "% · " + mem.usedGiB + "/" + mem.totalGiB + " GiB")];
                if (t.gpu !== undefined && t.gpu !== null) rows.push("GPU " + Math.round(t.gpu) + "°C");
                for (const gpu of d.gpus || []) rows.push(gpu.device + " " + gpu.percent + "%");
                return rows.join("\n");
            }
            color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11; lineHeight: 1.35
        }
    }
}
