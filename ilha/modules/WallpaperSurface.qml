import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services

PanelWindow {
    id: root
    WlrLayershell.namespace: "ilha-wallpaper"
    // Acima do fundo existente, abaixo de aplicativos; o provedor anterior continua intacto.
    WlrLayershell.layer: WlrLayer.Bottom
    exclusionMode: ExclusionMode.Ignore
    anchors { top:true; bottom:true; left:true; right:true }
    color: Theme.transparent
    mask: Region {}
    readonly property string monitor: screen ? screen.name : ""
    readonly property bool fullscreen: WallpaperState.options.pauseOnFullscreen !== false
        && ToplevelManager.toplevels.values.some(window => window.fullscreen
            && Array.from(window.screens).some(s => s.name === root.monitor))
    readonly property bool pausePlayback: WallpaperState.paused || fullscreen
    visible: WallpaperState.enabled && playback.mediaReady
    function report() {
        WallpaperState.report(monitor,{ready:playback.mediaReady,paused:pausePlayback,kind:WallpaperState.gif?"gif":"video",
            position:playback.position,duration:playback.duration});
    }
    onMonitorChanged: report()
    Component.onDestruction: WallpaperState.forget(monitor)
    WallpaperContent { id:playback; anchors.fill:parent; pausePlayback:root.pausePlayback }
    Timer { interval:1000; repeat:true; running:WallpaperState.enabled; onTriggered:root.report() }
}
