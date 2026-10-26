import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import qs.components
import qs.services

PanelWindow {
    id: root
    signal themesRequested()
    signal finished()
    WlrLayershell.namespace: "ilha-control-center"
    anchors { top: true; bottom: true; left: true; right: true }
    exclusiveZone: 0
    focusable: true
    color: Theme.transparent
    property real progress: 0
    property string confirmAction: ""
    readonly property var state: ControlCenterState.state
    readonly property var net: state.network || ({})
    readonly property var blue: state.bluetooth || ({})
    readonly property var audio: state.audio || ({})
    readonly property var light: state.brightness || ({})
    readonly property var power: state.profiles || ({})
    readonly property var session: state.session || ({})
    readonly property bool busy: ControlCenterState.busy
    readonly property bool oled: ThemeStore.config.theme === "oled"
    readonly property bool lightTheme: Theme.background.r * 0.21 + Theme.background.g * 0.72 + Theme.background.b * 0.07 > 0.5
    readonly property var player: Preferences.enabled("media") ? MediaState.playingPlayer || MediaState.players[0] || null : null
    readonly property var actionLabels: ({poweroff: "Desligar", reboot: "Reiniciar", suspend: "Suspender", lock: "Bloquear", logout: "Sair"})
    function close() { ControlCenterState.close(); }
    Component.onCompleted: progress = 1
    Connections {
        target: ControlCenterState
        function onOpenedChanged() { root.progress = ControlCenterState.opened && ControlCenterState.screenName === root.screen.name ? 1 : 0; }
        function onScreenNameChanged() { if (ControlCenterState.screenName !== root.screen.name) root.progress = 0; }
    }
    Behavior on progress {
        NumberAnimation {
            duration: Theme.morphDuration; easing.type: Easing.OutCubic
            onRunningChanged: if (!running && root.progress === 0) root.finished()
        }
    }
    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: root.close()
        MouseArea { anchors.fill: parent; onClicked: root.close() }

        // Sombras e brilho usam somente tokens; não há blur de textura na GPU do Qt.
        Repeater {
            model: 3
            Rectangle {
                required property int index
                x: board.x - (index + 1) * 3
                y: board.y + 4
                width: board.width + (index + 1) * 6
                height: board.height + (index + 1) * 5
                radius: board.radius + 4
                color: Theme.background
                opacity: root.oled ? 0 : 0.07 * root.progress
            }
        }
        Rectangle {
            id: board
            anchors.horizontalCenter: parent.horizontalCenter
            y: 8 + 52 * root.progress
            width: 174 + (Math.min(560, root.width - 24) - 174) * root.progress
            height: 36 + (Math.min(810, root.height - 78) - 36) * root.progress
            radius: 22 + 8 * root.progress
            clip: true
            color: Theme.transparent
            border.color: Theme.border
            border.width: 1
            MouseArea { anchors.fill: parent; onPressed: mouse => mouse.accepted = true }
            Rectangle {
                anchors.fill: parent; anchors.margins: 1; radius: parent.radius - 1
                color: Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b,
                    root.oled ? 1 : root.lightTheme ? Math.max(0.92, Theme.effectiveGlassOpacity) : Theme.effectiveGlassOpacity)
            }
            Rectangle {
                x: 28; y: 1; width: parent.width - 56; height: 1
                opacity: root.oled ? 0 : 1
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Theme.transparent }
                    GradientStop { position: 0.45; color: Qt.rgba(Theme.text.r, Theme.text.g, Theme.text.b, 0.4) }
                    GradientStop { position: 1; color: Theme.transparent }
                }
            }
            Column {
                id: header
                x: 22; y: 10; width: parent.width - 44; spacing: 10
                opacity: root.progress
                Rectangle { anchors.horizontalCenter: parent.horizontalCenter; width: 35; height: 4; radius: 2; color: Theme.secondaryText }
                Row {
                    width: parent.width; spacing: 12
                    Text { text: "Control Center"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 21; font.weight: Font.DemiBold }
                    ThemeButton { label: "Fechar"; onClicked: root.close() }
                }
                Text {
                    width: parent.width
                    text: root.state.battery && root.state.battery.available
                        ? root.state.battery.batteries.map(b => b.percent + "% · " + (b.status === "Charging" ? "Carregando" : b.status === "Full" ? "Completa" : "Na bateria")).join(" / ")
                        : "Sem bateria · alimentação externa"
                    color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10
                }
            }
            MouseArea {
                x: 0; y: 0; width: parent.width; height: 30
                property real startY: 0
                onPressed: mouse => startY = mouse.y
                onReleased: mouse => { if (mouse.y - startY < -30) root.close(); }
            }
            Flickable {
                id: scroll
                x: 22; y: 112; width: parent.width - 44; height: Math.max(0, parent.height - y - 18)
                contentHeight: content.height
                clip: true; opacity: root.progress
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                    contentItem: Rectangle { implicitWidth: 4; radius: 2; color: Theme.accent; opacity: 0.65 }
                    background: Item {}
                }
                Column {
                    id: content
                    width: scroll.width; spacing: 16
                    Grid {
                        width: parent.width; columns: 2; spacing: 10
                        ControlTile {
                            width: (parent.width - 10) / 2
                            title: "Wi-Fi"; symbol: "󰖩"; active: !!root.net.wifi
                            detail: !root.net.available ? "Indisponível" : !root.net.wifiHardware ? "Bloqueado no hardware" : root.net.wifi ? (root.net.connection || "Ligado") : "Desligado"
                            enabled: !!root.net.available && !!root.net.wifiHardware && !root.busy && !root.state.airplaneManaged
                            onClicked: ControlCenterState.action("wifi", !root.net.wifi)
                        }
                        ControlTile {
                            width: (parent.width - 10) / 2
                            title: "Bluetooth"; symbol: "󰂯"; active: !!root.blue.powered
                            detail: !root.blue.available ? "Sem adaptador" : root.blue.powered ? root.blue.connected + " conectado(s)" : "Desligado"
                            enabled: !!root.blue.available && !root.busy && !root.state.airplaneManaged
                            onClicked: ControlCenterState.action("bluetooth", !root.blue.powered)
                        }
                        ControlTile {
                            width: (parent.width - 10) / 2
                            title: "Modo avião"; symbol: "󰀝"; active: !!root.state.airplane
                            detail: root.state.airplaneManaged ? "Restaurar rádios anteriores" : "Desligar Wi-Fi, WWAN e Bluetooth"
                            enabled: !!root.net.available && !root.busy
                            onClicked: ControlCenterState.action("airplane", !root.state.airplaneManaged)
                        }
                        ControlTile {
                            width: (parent.width - 10) / 2
                            title: "Não perturbe"; symbol: "󰂛"; active: NotificationState.doNotDisturb
                            detail: active ? "Notificações silenciosas" : "Notificações permitidas"
                            onClicked: NotificationState.toggleDoNotDisturb()
                        }
                    }
                    Row {
                        width: parent.width; spacing: 12
                        ThemeButton {
                            label: root.audio.muted ? "󰝟" : "󰕾"
                            enabled: !!root.audio.available && !root.busy
                            onClicked: ControlCenterState.action("mute", !root.audio.muted)
                        }
                        Column {
                            width: parent.width - 68
                            Text { text: root.audio.available ? "Volume · " + Math.round(volume.value) + "%" : "Áudio indisponível"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                            ThemeSlider {
                                id: volume; width: parent.width; from: 0; to: 100; stepSize: 1
                                property real desiredValue: 0
                                enabled: !!root.audio.available && !root.busy
                                Binding { target: volume; property: "value"; value: root.audio.volume || 0; when: !volume.pressed; restoreMode: Binding.RestoreNone }
                                onMoved: desiredValue = value
                                onPressedChanged: if (!pressed && enabled) ControlCenterState.action("volume", desiredValue)
                                Keys.onReleased: event => { if ([Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End].includes(event.key)) ControlCenterState.action("volume", value); }
                            }
                        }
                    }
                    Column {
                        width: parent.width
                        Text { text: root.light.available ? "Brilho da tela integrada · " + Math.round(brightness.value) + "%" : "Brilho indisponível neste monitor"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                        ThemeSlider {
                            id: brightness; width: parent.width; from: 1; to: 100; stepSize: 1
                            property real desiredValue: 1
                            enabled: !!root.light.available && !root.busy
                            Binding { target: brightness; property: "value"; value: root.light.value || 1; when: !brightness.pressed; restoreMode: Binding.RestoreNone }
                            onMoved: desiredValue = value
                            onPressedChanged: if (!pressed && enabled) ControlCenterState.action("brightness", desiredValue)
                            Keys.onReleased: event => { if ([Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End].includes(event.key)) ControlCenterState.action("brightness", value); }
                        }
                    }
                    Column {
                        width: parent.width; spacing: 8
                        Text { text: "Perfil de energia"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                        Row {
                            spacing: 8
                            Repeater {
                                model: root.power.profiles || []
                                ThemeButton {
                                    required property string modelData
                                    label: ({ balanced: "Equilibrado", "power-saver": "Economia", performance: "Desempenho" })[modelData]
                                    emphasized: root.power.current === modelData
                                    enabled: !root.busy
                                    onClicked: ControlCenterState.action("profile", modelData)
                                }
                            }
                            Text { visible: !root.power.available; text: "Indisponível"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                        }
                    }
                    Rectangle {
                        width: parent.width; height: 76; radius: 17; color: Theme.elevatedSurface
                        MediaWidget { x: 14; y: 11; width: parent.width - 28; player: root.player; expanded: true; visible: !!root.player }
                        Text { anchors.centerIn: parent; visible: !root.player; text: "Nenhuma mídia disponível"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    }
                    Column {
                        width: parent.width; spacing: 8
                        Row {
                            spacing: 18
                            Text { text: "Seu tema"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13 }
                            ThemeButton { label: "Editar cores"; onClicked: { root.themesRequested(); root.close(); } }
                        }
                        Flickable {
                            width: parent.width; height: 84; contentWidth: themesRow.width; clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            Row {
                                id: themesRow; spacing: 10
                                Repeater { model: ThemeStore.themes; ThemeCard { required property var modelData; themeData: modelData; onChosen: ThemeStore.select(themeData.id) } }
                            }
                        }
                    }
                    Row {
                        spacing: 10
                        ThemeButton { label: "Configurações"; onClicked: { SettingsState.open("modules"); root.close(); } }
                        ThemeButton { label: "HyprMod ↗"; onClicked: { SettingsState.launchHyprmod(); } }
                    }
                    Text {
                        width: parent.width; visible: SettingsState.message.length > 0
                        text: SettingsState.message; wrapMode: Text.WordWrap; textFormat: Text.PlainText
                        color: Theme.warning; font.family: Theme.fontFamily; font.pixelSize: 11
                    }
                    Text {
                        width: parent.width; visible: ControlCenterState.message.length > 0
                        text: ControlCenterState.message; wrapMode: Text.WordWrap; textFormat: Text.PlainText
                        color: Theme.error; font.family: Theme.fontFamily; font.pixelSize: 11
                    }
                    Flow {
                        width: parent.width; spacing: 8
                        Repeater {
                            model: ["lock", "suspend", "logout", "reboot", "poweroff"]
                            ThemeButton {
                                required property string modelData
                                label: root.actionLabels[modelData]
                                enabled: !!root.session[modelData] && !root.busy
                                onClicked: root.confirmAction = modelData
                            }
                        }
                    }
                    Column {
                        width: parent.width; spacing: 8; visible: root.confirmAction !== ""
                        Text { text: (root.actionLabels[root.confirmAction] || "") + " agora?"; color: Theme.warning; font.family: Theme.fontFamily; font.pixelSize: 12 }
                        Row {
                            spacing: 8
                            ThemeButton {
                                label: "Confirmar"; emphasized: true; enabled: !root.busy
                                onClicked: { const action = root.confirmAction; root.confirmAction = ""; ControlCenterState.action(action, null, true); }
                            }
                            ThemeButton { label: "Cancelar"; onClicked: root.confirmAction = "" }
                        }
                    }
                }
            }
        }
    }
}
