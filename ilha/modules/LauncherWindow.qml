import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import Quickshell.Widgets
import qs.components
import qs.services

PanelWindow {
    id: root
    signal finished()
    WlrLayershell.namespace: "ilha-launcher"
    anchors { top:true; bottom:true; left:true; right:true }
    exclusiveZone: 0
    focusable: true
    color: Theme.transparent
    property real progress: 0
    readonly property real expandedHeight: Math.min(height - board.y - 24,
        Math.max(258, 186 + Math.min(7, LauncherState.results.length) * 58))
    SystemClock { id: clock; precision: SystemClock.Minutes }
    Component.onCompleted: { progress = 1; Qt.callLater(() => input.forceActiveFocus()); }
    Connections {
        target: LauncherState
        function onOpenedChanged() { root.progress = LauncherState.opened && LauncherState.screenName === root.screen.name ? 1 : 0; }
        function onScreenNameChanged() { if (LauncherState.screenName !== root.screen.name) root.progress = 0; }
        function onSelectedIndexChanged() { list.positionViewAtIndex(LauncherState.selectedIndex, ListView.Contain); }
    }
    Behavior on progress {
        NumberAnimation {
            duration: Theme.morphDuration; easing.type: Easing.OutCubic
            onRunningChanged: if (!running && root.progress === 0) root.finished()
        }
    }
    Item {
        anchors.fill: parent
        MouseArea { anchors.fill: parent; onClicked: LauncherState.close() }
        Rectangle {
            id: board
            anchors.horizontalCenter: parent.horizontalCenter
            y: ThemeStore.config.island ? ThemeStore.config.island.topMargin : 8
            width: LauncherState.originWidth + (Math.min(Math.max(590, LauncherState.originWidth), root.width - 24) - LauncherState.originWidth) * root.progress
            height: LauncherState.originHeight + (root.expandedHeight - LauncherState.originHeight) * root.progress
            radius: LauncherState.originRadius + (28 - LauncherState.originRadius) * root.progress
            color: Qt.rgba(Theme.surface.r,Theme.surface.g,Theme.surface.b,Theme.effectiveGlassOpacity)
            border.color: Theme.border; border.width: 1
            clip: true
            Behavior on height { enabled: root.progress === 1; NumberAnimation { duration: Theme.contentDuration; easing.type:Easing.OutCubic } }
            MouseArea { anchors.fill: parent; onPressed: mouse => mouse.accepted = true }
            Item {
                anchors.fill: parent
                opacity: root.progress
                Row {
                    x: 22; y: 10; spacing: 12
                    DeviceBattery { anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: Preferences.enabled("clock")
                        text: Qt.formatDateTime(clock.date, "HH:mm")
                        color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 12
                    }
                    WorkspaceDots {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: Preferences.enabled("workspaces")
                        targetScreen: root.screen; expanded: false; activityCompact: true; style: "dots"; maxVisible: 3
                        onWorkspaceActivated: input.forceActiveFocus()
                    }
                    PrivacyWidget { anchors.verticalCenter: parent.verticalCenter; expanded: false }
                    PhoneWidget { anchors.verticalCenter: parent.verticalCenter; expanded: false }
                }
                Text {
                    anchors.right: parent.right; anchors.rightMargin: 23; y: 12
                    text: "×"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 18
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: LauncherState.close() }
                }
                TextField {
                    id: input
                    x: 18; y: 41; width: parent.width - 36; height: 45
                    text: LauncherState.query
                    maximumLength: 2048
                    placeholderText: "Pesquisar apps · = cálculo · : clipboard · > ações"
                    color: Theme.text; placeholderTextColor: Theme.secondaryText
                    selectionColor: Theme.accent; selectedTextColor: Theme.background
                    font.family: Theme.fontFamily; font.pixelSize: 13
                    background: Rectangle { radius: 16; color: Theme.elevatedSurface; border.color: input.activeFocus ? Theme.accent : Theme.border }
                    onTextEdited: LauncherState.query = text
                    onAccepted: LauncherState.activate()
                    Keys.onDownPressed: LauncherState.move(1)
                    Keys.onUpPressed: LauncherState.move(-1)
                    Keys.onEscapePressed: LauncherState.close()
                    Keys.onTabPressed: LauncherState.move(1)
                    Keys.onBacktabPressed: LauncherState.move(-1)
                }
                Row {
                    x: 18; y: 97; spacing: 7
                    Repeater {
                        model: [{mode:"apps",name:"Apps"},{mode:"calculator",name:"Calculadora"},
                                {mode:"clipboard",name:"Clipboard"},{mode:"commands",name:"Ações"}]
                        ThemeButton {
                            required property var modelData
                            label: modelData.name; emphasized: LauncherState.mode === modelData.mode
                            onClicked: { LauncherState.setMode(modelData.mode); input.forceActiveFocus(); }
                        }
                    }
                }
                ListView {
                    id: list
                    x: 14; y: 141; width: parent.width - 28; height: Math.max(0, parent.height - y - 37)
                    model: LauncherState.results
                    currentIndex: LauncherState.selectedIndex
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    highlightMoveDuration: Theme.contentDuration
                    highlightResizeDuration: Theme.contentDuration
                    highlight: Rectangle { radius: 14; color: Theme.elevatedSurface; border.color: Theme.border }
                    delegate: Item {
                        id: row
                        required property var modelData
                        required property int index
                        width: list.width; height: 58
                        Rectangle {
                            x: 12; y: 12; width: 34; height: 34; radius: 10
                            color: Theme.elevatedSurface
                            IconImage {
                                id: entryIcon
                                anchors.centerIn: parent; width: 26; height: 26
                                source: row.modelData.icon ? Quickshell.iconPath(row.modelData.icon, true) : ""
                                visible: !row.modelData.thumbnail
                            }
                            Image {
                                id: wallpaperPreview
                                anchors.fill: parent
                                visible: !!row.modelData.thumbnail
                                source: row.modelData.thumbnail || ""
                                sourceSize.width: 100; sourceSize.height: 70
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                            Text {
                                anchors.centerIn: parent
                                visible: row.modelData.thumbnail ? wallpaperPreview.status !== Image.Ready : entryIcon.source.toString().length === 0
                                text: row.modelData.thumbnail && wallpaperPreview.status === Image.Loading ? "…" : row.modelData.kind === "calculator" ? "=" : "›"
                                color: Theme.accent; font.family: Theme.fontFamily; font.pixelSize: 18
                            }
                        }
                        Text {
                            x: 58; y: 10; width: parent.width - 105
                            text: row.modelData.title; textFormat: Text.PlainText; elide: Text.ElideRight
                            color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13
                        }
                        Text {
                            x: 58; y: 32; width: parent.width - 105
                            text: row.modelData.swatches ? "" : row.modelData.detail; textFormat: Text.PlainText; elide: Text.ElideRight
                            color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10
                        }
                        Row {
                            x: 58; y: 34; spacing: 5
                            Repeater {
                                model: row.modelData.swatches || []
                                Rectangle {
                                    required property string modelData
                                    width: 22; height: 10; radius: 3
                                    color: modelData; border.color: Theme.border
                                }
                            }
                        }
                        Text {
                            anchors.right: parent.right; anchors.rightMargin: 13; anchors.verticalCenter: parent.verticalCenter
                            text: "↵"; visible: row.index === LauncherState.selectedIndex
                            color: Theme.accent; font.family: Theme.fontFamily; font.pixelSize: 15
                        }
                        MouseArea {
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onPositionChanged: LauncherState.selectedIndex = row.index
                            onClicked: LauncherState.activate(row.index)
                        }
                    }
                }
                Text {
                    x: 24; y: 160; width: parent.width - 48
                    visible: LauncherState.results.length === 0
                    text: LauncherState.message || (LauncherState.readBusy ? "Consultando…" : LauncherState.mode === "calculator"
                        ? "Digite uma expressão. Exemplo: = sqrt(144) + 2"
                        : LauncherState.mode === "commands" ? "Nenhum resultado. Coloque wallpapers em ~/Pictures/Wallpapers."
                        : LauncherState.mode === "clipboard" ? "Nenhum item encontrado no histórico." : "Nenhum aplicativo encontrado.")
                    color: LauncherState.message ? Theme.warning : Theme.secondaryText
                    font.family: Theme.fontFamily; font.pixelSize: 12
                    wrapMode: Text.WordWrap; textFormat: Text.PlainText
                }
                Text {
                    x: 22; anchors.bottom: parent.bottom; anchors.bottomMargin: 12
                    width: parent.width - 110
                    text: LauncherState.message || "↑↓ selecionar · Enter confirmar · Esc fechar"
                    color: LauncherState.message ? Theme.warning : Theme.secondaryText
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    font.family: Theme.fontFamily; font.pixelSize: 10
                }
                Text {
                    anchors.right: parent.right; anchors.rightMargin: 24
                    anchors.bottom: parent.bottom; anchors.bottomMargin: 12
                    text: "Temas →"; color: Theme.accent; font.family: Theme.fontFamily; font.pixelSize: 10
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { LauncherState.close(); SettingsState.open("themes"); } }
                }
            }
        }
    }
}
