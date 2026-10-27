import QtQuick
import QtQuick.Controls
import qs.services

Column {
    id: root
    signal browseRequested()
    spacing: 14
    Text { text:"Wallpaper animado"; color:Theme.text; font.family:Theme.fontFamily; font.pixelSize:20 }
    Text {
        width:parent.width; wrapMode:Text.WordWrap
        text:"Vídeos e GIFs de ~/Pictures/Wallpapers. Sem áudio; o fundo anterior reaparece ao desativar."
        color:Theme.secondaryText; font.family:Theme.fontFamily; font.pixelSize:12
    }
    TextField {
        id: path
        width:parent.width
        text:WallpaperState.path
        placeholderText:"~/Pictures/Wallpapers/animacao.mp4"
        color:Theme.text; placeholderTextColor:Theme.secondaryText
        selectionColor:Theme.accent; selectedTextColor:Theme.background
        font.family:Theme.fontFamily
        background:Rectangle { radius:10; color:Theme.elevatedSurface; border.color:Theme.border }
    }
    Row {
        spacing:10
        ThemeButton { label:WallpaperState.busy?"Preparando…":"Aplicar GIF/vídeo"; enabled:!WallpaperState.busy && path.text.length>0; onClicked:WallpaperState.select(path.text) }
        ThemeButton { label:"Escolher no launcher"; enabled:Preferences.enabled("launcher"); onClicked:root.browseRequested() }
    }
    Row {
        spacing:10
        ThemeButton { label:WallpaperState.options.paused?"Retomar":"Pausar"; enabled:WallpaperState.enabled; onClicked:WallpaperState.pause(!WallpaperState.options.paused) }
        ThemeButton { label:"Desativar fundo animado"; enabled:WallpaperState.enabled; onClicked:WallpaperState.stop() }
    }
    Repeater {
        model:[{key:"pauseOnBattery",title:"Pausar na bateria",description:"Reduzir consumo quando o computador estiver descarregando"},
            {key:"pauseOnFullscreen",title:"Pausar em tela cheia",description:"Pausar no monitor com jogo ou aplicativo em tela cheia"},
            {key:"pauseOnPerformance",title:"Pausar no modo desempenho",description:"Liberar recursos para os aplicativos"}]
        SettingsToggle {
            required property var modelData
            width:parent.width
            label:modelData.title; description:modelData.description
            checked:WallpaperState.options[modelData.key] !== false
            onToggled: { const values={};values[modelData.key]=!checked;ThemeStore.setPreferences({wallpaper:values}); }
        }
    }
    Text {
        width:parent.width; wrapMode:Text.WordWrap
        text:WallpaperState.message || (WallpaperState.enabled ? WallpaperState.paused ? "Pausado por preferência ou economia de recursos." : "Ativo. Tela cheia pode pausar cada monitor separadamente." : "O provedor de wallpaper anterior continua ativo.")
        color:WallpaperState.message?Theme.error:Theme.secondaryText
        font.family:Theme.fontFamily; font.pixelSize:12
    }
}
