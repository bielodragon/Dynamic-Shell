import QtQuick
import QtQuick.Controls
import Quickshell
import qs.components
import qs.services

FloatingWindow {
    id: root
    title: "Configurações da Ilha"
    implicitWidth: 980; implicitHeight: 880
    minimumSize: Qt.size(900, 650)
    color: Theme.background
    onClosed: SettingsState.opened = false
    readonly property var modules: [
        {key:"launcher", title:"Lançador", description:"Aplicativos, calculadora, clipboard e comandos a partir da ilha"},
        {key:"clock", title:"Relógio", description:"Mostrar o horário na ilha"},
        {key:"workspaces", title:"Workspaces", description:"Indicadores, clique e navegação entre áreas"},
        {key:"notifications", title:"Notificações do desktop", description:"Servidor e bolhas da Ilha; não altera outros shells"},
        {key:"media", title:"Mídia", description:"MPRIS na ilha e no Control Center"},
        {key:"activities", title:"Atividades de desenvolvimento", description:"Receber estados e progresso por CLI/IPC"},
        {key:"privacy", title:"Privacidade e gravação", description:"Observar PipeWire e OBS; não interrompe capturas"},
        {key:"phone", title:"KDE Connect", description:"Bateria e eventos do celular; não desconecta o aparelho"}
    ]
    Item {
        anchors.fill: parent; focus: true
        Keys.onEscapePressed: SettingsState.opened = false
        Row {
            id: header
            x: 24; y: 20; spacing: 16
            Text { text: "Configurações da Ilha"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 22; font.weight: Font.DemiBold }
            ThemeButton { label: "Fechar"; onClicked: SettingsState.opened = false }
        }
        Row {
            x: 24; y: 70; spacing: 10
            Repeater {
                model: [{key:"modules",title:"Módulos"},{key:"appearance",title:"Aparência"},{key:"themes",title:"Temas e cores"}]
                ThemeButton { required property var modelData; label: modelData.title; emphasized: SettingsState.page === modelData.key; onClicked: SettingsState.page = modelData.key }
            }
            ThemeButton { label: "HyprMod ↗"; onClicked: SettingsState.launchHyprmod() }
        }
        Text {
            x: 24; y: 115; width: parent.width - 48
            text: SettingsState.message || ThemeStore.message || "As alterações são aplicadas e salvas automaticamente."
            color: SettingsState.message || ThemeStore.messageIsError ? Theme.error : Theme.secondaryText
            font.family: Theme.fontFamily; font.pixelSize: 11; textFormat: Text.PlainText; elide: Text.ElideRight
        }
        Loader {
            x: 16; y: 143; width: parent.width - 32; height: parent.height - y - 16
            active: SettingsState.page === "themes"
            sourceComponent: ThemeEditor { onCloseRequested: SettingsState.page = "appearance" }
        }
        Flickable {
            x: 24; y: 148; width: parent.width - 48; height: parent.height - y - 24
            visible: SettingsState.page !== "themes"
            clip: true; contentHeight: column.height
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: column
                width: parent.width; spacing: 14
                Column {
                    width: parent.width; spacing: 10; visible: SettingsState.page === "modules"
                    Repeater {
                        model: root.modules
                        SettingsToggle {
                            required property var modelData
                            label: modelData.title; description: modelData.description
                            checked: Preferences.enabled(modelData.key)
                            onToggled: Preferences.setModule(modelData.key, !checked)
                        }
                    }
                    Text { width: parent.width; text: "A ilha e o Control Center continuam acessíveis para reativar módulos. Desativar privacidade apenas esconde os indicadores e para seus observadores; câmera, áudio e gravações continuam sob controle dos aplicativos."; color: Theme.warning; font.family: Theme.fontFamily; font.pixelSize: 11; wrapMode: Text.WordWrap }
                }
                Column {
                    width: parent.width; spacing: 14; visible: SettingsState.page === "appearance"
                    SettingsToggle {
                        label: "Cantos arredondados da tela"; description: "Decoração sem capturar cliques; aplicada em cada monitor"
                        checked: !ThemeStore.config.corners || ThemeStore.config.corners.enabled !== false
                        onToggled: ThemeStore.setPreferences({corners:{enabled:!checked}})
                    }
                    Text { text: "Raio dos cantos: " + ((ThemeStore.config.corners || {}).radius || 18); color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider { width: parent.width; from: 1; to: 48; stepSize: 1; value: (ThemeStore.config.corners || {}).radius || 18; onPressedChanged: if (!pressed) ThemeStore.setPreferences({corners:{radius:Math.round(value)}}) }
                    SettingsToggle {
                        label: "Animações"; description: "Desligue para mudanças imediatas e menor movimento"
                        checked: Preferences.animationsEnabled
                        onToggled: ThemeStore.setPreferences({animations:{enabled:!checked}})
                    }
                    Text { text: "Duração das transições (menor = mais rápido)"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 12 }
                    ThemeSlider {
                        width: parent.width; from: 0.5; to: 2; stepSize: 0.1
                        enabled: Preferences.animationsEnabled
                        value: (ThemeStore.config.animations || {}).scale || 1
                        onPressedChanged: if (!pressed) ThemeStore.setPreferences({animations:{scale:value}})
                    }
                    Text { text: "Vidro e desfoque"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 16 }
                    Text { text: "Opacidade: " + Math.round(Theme.glassOpacity * 100) + "%"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider { width: parent.width; from: 0.55; to: 1; stepSize: .01; value: Theme.glassOpacity; enabled: ThemeStore.config.theme !== "oled"; onPressedChanged: if (!pressed) ThemeStore.setOverrides({glassOpacity:value}) }
                    Text { text: "Intensidade do vidro desfocado: " + Math.round(Theme.blurIntensity * 100) + "%"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider { width: parent.width; from: 0; to: 1; stepSize: .01; value: Theme.blurIntensity; enabled: ThemeStore.config.theme !== "oled"; onPressedChanged: if (!pressed) ThemeStore.setOverrides({blurIntensity:value}) }
                    Text { width: parent.width; text: "OLED mantém preto sólido. A intensidade controla quanto do fundo desfocado aparece; o raio do blur é global do Hyprland."; wrapMode: Text.WordWrap; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    Text { text: "Workspaces"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 16 }
                    Row {
                        spacing: 10
                        ThemeButton { label: "Ícones"; emphasized: ThemeStore.config.workspaceStyle === "icons"; onClicked: ThemeStore.setWorkspaceStyle("icons") }
                        ThemeButton { label: "Pontos"; emphasized: ThemeStore.config.workspaceStyle === "dots"; onClicked: ThemeStore.setWorkspaceStyle("dots") }
                    }
                    Text { text: "Máximo de workspaces visíveis: " + (ThemeStore.config.maxVisibleWorkspaces || 6); color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider { width: parent.width; from: 1; to: 12; stepSize: 1; value: ThemeStore.config.maxVisibleWorkspaces || 6; onPressedChanged: if (!pressed) ThemeStore.setPreferences({maxVisibleWorkspaces:Math.round(value)}) }
                    ThemeButton { label: "Escolher tema e editar cores →"; onClicked: SettingsState.page = "themes" }
                    Text { text: "Sincronização opcional"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 16 }
                    Text { width: parent.width; text: "Ative somente as integrações desejadas. Outros gerenciadores de tema podem reaplicar suas próprias cores. Desligar interrompe a sincronização futura."; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11; wrapMode: Text.WordWrap }
                    Repeater {
                        model: [{key:"portal",title:"Preferência claro/escuro",description:"GTK e aplicativos Qt que seguem o portal do desktop"},
                            {key:"kitty",title:"Cores do Kitty",description:"Adiciona include com backup; recarregue janelas já abertas"},
                            {key:"hyprland",title:"Bordas do Hyprland",description:"Atualiza destaque e borda inativa na sessão"},
                            {key:"wallpaper",title:"Wallpaper associado ao tema",description:"Usa a imagem definida abaixo para cada tema"}]
                        SettingsToggle {
                            required property var modelData
                            label: modelData.title; description: modelData.description
                            checked: !!(ThemeStore.config.sync || {})[modelData.key]
                            onToggled: { const values = {}; values[modelData.key] = !checked; ThemeStore.setPreferences({sync:values}); }
                        }
                    }
                    TextField {
                        id: wallpaperPath
                        width: parent.width
                        placeholderText: "~/Pictures/Wallpapers/imagem.png"
                        text: (ThemeStore.config.wallpapers || {})[ThemeStore.config.theme] || ""
                        color: Theme.text; placeholderTextColor: Theme.secondaryText
                        selectionColor: Theme.accent; selectedTextColor: Theme.background
                        font.family: Theme.fontFamily
                        background: Rectangle { radius: 8; color: Theme.elevatedSurface; border.color: Theme.border }
                    }
                    ThemeButton {
                        label: "Associar wallpaper ao tema atual"
                        onClicked: { const values = {}; values[ThemeStore.config.theme] = wallpaperPath.text; ThemeStore.setPreferences({wallpapers:values}); }
                    }
                    Text { width: parent.width; text: ThemeSync.message; visible: text.length > 0; wrapMode: Text.WordWrap; color: Theme.warning; font.family: Theme.fontFamily; font.pixelSize: 11 }
                }
            }
        }
    }
}
