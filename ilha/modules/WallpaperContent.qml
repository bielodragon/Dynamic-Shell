import QtQuick
import QtMultimedia
import qs.services

Item {
    id: root
    property bool pausePlayback: WallpaperState.paused
    readonly property bool gif: WallpaperState.gif
    readonly property bool mediaReady: gif ? animation.status === Image.Ready : player.hasVideo && player.error === MediaPlayer.NoError
    readonly property int position: gif ? animation.currentFrame : player.position
    readonly property int duration: gif ? animation.frameCount : player.duration
    function sync() { if (!WallpaperState.enabled) player.stop(); else if (!gif) { if (pausePlayback) player.pause(); else player.play(); } }
    onPausePlaybackChanged: sync()
    onMediaReadyChanged: sync()
    Component.onCompleted: sync()
    MediaPlayer {
        id: player
        source: WallpaperState.enabled && !root.gif ? WallpaperState.source : ""
        loops: MediaPlayer.Infinite
        activeAudioTrack: -1
        activeSubtitleTrack: -1
        audioOutput: AudioOutput { muted:true; volume:0 }
        videoOutput: output
        onMediaStatusChanged: if (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia) root.sync()
        onErrorOccurred: (error,errorString) => { if (WallpaperState.enabled && !root.gif && source.toString()) WallpaperState.failed(errorString); }
    }
    VideoOutput { id:output; anchors.fill:parent; visible:!root.gif; fillMode:VideoOutput.PreserveAspectCrop }
    AnimatedImage {
        id: animation
        anchors.fill:parent
        visible:root.gif
        source:WallpaperState.enabled && root.gif ? WallpaperState.source : ""
        sourceSize.width:root.width
        fillMode:Image.PreserveAspectCrop
        cache:false
        playing:WallpaperState.enabled && root.gif
        paused:root.pausePlayback
        onStatusChanged: if (WallpaperState.enabled && root.gif && source.toString() && status === Image.Error) WallpaperState.failed("GIF inválido ou sem suporte.")
    }
}
