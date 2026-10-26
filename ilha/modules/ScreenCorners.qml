import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services

Scope {
    id: root
    required property var targetScreen
    readonly property var options: ThemeStore.config.corners || ({enabled:true,radius:18})
    Variants {
        model: root.options.enabled ? [0,1,2,3] : []
        delegate: PanelWindow {
            id: corner
            required property var modelData
            screen: root.targetScreen
            WlrLayershell.namespace: "ilha-corners"
            WlrLayershell.layer: WlrLayer.Overlay
            exclusionMode: ExclusionMode.Ignore
            anchors.top: modelData < 2
            anchors.bottom: modelData >= 2
            anchors.left: modelData === 0 || modelData === 3
            anchors.right: modelData === 1 || modelData === 2
            implicitWidth: root.options.radius || 18
            implicitHeight: implicitWidth
            color: Theme.transparent
            // Superfície sem região de entrada: cliques atravessam os cantos.
            mask: Region {}
            Canvas {
                id: canvas
                anchors.fill: parent
                rotation: corner.modelData * 90
                property color ink: Theme.background
                onInkChanged: requestPaint()
                onWidthChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d"), r = width;
                    ctx.reset(); ctx.fillStyle = ink;
                    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(r,0);
                    ctx.arc(r,r,r,-Math.PI/2,-Math.PI,true);
                    ctx.closePath(); ctx.fill();
                }
            }
        }
    }
}
