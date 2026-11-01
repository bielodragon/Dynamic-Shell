import QtQuick
import QtQuick.Controls
import qs.services

Item {
    id: root
    readonly property bool wifi: ConnectivityState.mode === "wifi"
    readonly property var state: ConnectivityState.state
    property var selected: null
    property bool showPassword: false
    property string confirmation: ""
    onSelectedChanged: if (selected) Qt.callLater(() => listScroll.contentY=Math.max(0,listScroll.contentHeight-listScroll.height))
    function reset() { selected=null;password.text="";pin.text="";confirmation="";showPassword=false; }
    Component.onDestruction: { password.text="";pin.text=""; }
    Connections {
        target:ConnectivityState
        function onModeChanged() { root.reset(); }
        function onChallengeChanged() { if (ConnectivityState.challenge.kind) Qt.callLater(() => listScroll.contentY=Math.max(0,listScroll.contentHeight-listScroll.height)); }
    }
    Column {
        id: header
        width:parent.width;spacing:12
        Row {
            spacing:10
            ThemeButton { label:"‹ Voltar";onClicked: { root.reset();ConnectivityState.close(); } }
            Text { text:root.wifi ? "Redes Wi-Fi" : "Bluetooth";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:19;anchors.verticalCenter:parent.verticalCenter }
        }
        Row {
            spacing:8
            ThemeButton {
                label:root.state.enabled ? "Desligar" : "Ligar"
                enabled:!!root.state.available && !ConnectivityState.busy && !ControlCenterState.state.airplaneManaged && (!root.wifi || !!root.state.hardware)
                onClicked:ConnectivityState.action(root.wifi?"wifi-power":"blue-power",{enabled:!root.state.enabled})
            }
            ThemeButton {
                label:root.wifi ? "Atualizar redes" : root.state.discovering ? "Buscando…" : "Buscar dispositivos"
                enabled:!!root.state.enabled && !ConnectivityState.busy && !ControlCenterState.state.airplaneManaged
                onClicked:ConnectivityState.action(root.wifi?"wifi-scan":"blue-scan")
            }
        }
        Text {
            width:parent.width;wrapMode:Text.WordWrap;textFormat:Text.PlainText
            text:ControlCenterState.state.airplaneManaged ? "Desative o modo avião para controlar os rádios."
                : !ConnectivityState.ready ? "Carregando…" : !root.state.available ? (root.state.error || "Nenhum adaptador disponível.")
                : root.wifi && !root.state.hardware ? "Wi-Fi bloqueado no hardware." : !root.state.enabled ? "Rádio desligado." : ConnectivityState.busy ? "Operação em andamento…" : root.wifi ? "Escolha uma rede para conectar ou desconectar." : "Selecione um dispositivo. A busca para após 30 segundos."
            color:Theme.secondaryText;font.family:Theme.fontFamily;font.pixelSize:11
        }
        Text { width:parent.width;visible:text.length>0;text:ConnectivityState.message;color:Theme.error;font.family:Theme.fontFamily;font.pixelSize:11;wrapMode:Text.WordWrap;textFormat:Text.PlainText }
    }
    Flickable {
        id:listScroll
        y:header.height+12;width:parent.width;height:Math.max(0,parent.height-y)
        contentHeight:body.height;clip:true;boundsBehavior:Flickable.StopAtBounds
        ScrollBar.vertical:ScrollBar { policy:ScrollBar.AsNeeded;visible:listScroll.contentHeight>listScroll.height;contentItem:Rectangle { implicitWidth:4;radius:2;color:Theme.accent } background:Item{} }
        Column {
            id:body;width:parent.width;spacing:10
            Repeater {
                model:root.wifi ? (root.state.networks || []) : (root.state.devices || [])
                delegate:ControlTile {
                    required property var modelData
                    width:body.width
                    title:root.wifi ? modelData.ssid : modelData.name
                    symbol:root.wifi ? "󰖩" : "󰂯"
                    active:root.selected && root.selected.id===modelData.id
                    detail:root.wifi ? [modelData.connected?"Conectada":modelData.connecting?"Conectando":modelData.saved?"Salva":"Disponível",modelData.strength+"%",modelData.security,modelData.interface].join(" · ")
                        : [modelData.connected?"Conectado":modelData.paired?"Pareado":"Disponível",modelData.trusted?"Confiável":"",modelData.blocked?"Bloqueado":"",modelData.battery!==null?modelData.battery+"%":""].filter(Boolean).join(" · ")
                    onClicked: { root.reset();root.selected=modelData; }
                }
            }
            Text { width:parent.width;visible:ConnectivityState.ready && !!root.state.enabled && (root.wifi ? !(root.state.networks || []).length : !(root.state.devices || []).length);text:root.wifi ? "Nenhuma rede encontrada. Clique em Atualizar redes." : "Nenhum dispositivo encontrado. Coloque o dispositivo em modo de pareamento e clique em Buscar dispositivos.";color:Theme.secondaryText;font.family:Theme.fontFamily;font.pixelSize:12;wrapMode:Text.WordWrap }
            Column {
                width:parent.width;spacing:10;visible:root.selected!==null
                Text { width:parent.width;text:root.selected ? (root.wifi ? root.selected.ssid : root.selected.name) : "";textFormat:Text.PlainText;color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:15;wrapMode:Text.WordWrap }
                TextField {
                    id:password;objectName:"wifiPassword";width:parent.width;visible:root.wifi && !!root.selected && ["wpa-psk","sae"].includes(root.selected.security)
                    placeholderText:root.selected && root.selected.saved ? "Senha (vazio usa o perfil salvo)" : "Senha da rede"
                    echoMode:root.showPassword ? TextInput.Normal : TextInput.Password
                    maximumLength:1024;color:Theme.text;placeholderTextColor:Theme.secondaryText;selectionColor:Theme.accent;selectedTextColor:Theme.background;font.family:Theme.fontFamily
                    background:Rectangle { radius:10;color:Theme.elevatedSurface;border.color:Theme.border }
                }
                Row {
                    visible:root.wifi && !!root.selected;spacing:8
                    ThemeButton { visible:password.visible;label:root.showPassword?"Ocultar senha":"Mostrar senha";onClicked:root.showPassword=!root.showPassword }
                    ThemeButton { id:save;property bool checked:true;label:checked?"Salvar nova conexão: sim":"Salvar nova conexão: não";onClicked:checked=!checked }
                }
                Text { visible:root.wifi && !!root.selected && ["enterprise","wep"].includes(root.selected.security);width:parent.width;text:"Para WEP/802.1X, configure um perfil no NetworkManager; perfis existentes podem ser usados aqui.";color:Theme.warning;font.family:Theme.fontFamily;font.pixelSize:11;wrapMode:Text.WordWrap }
                Flow {
                    width:parent.width;spacing:8
                    ThemeButton {
                        objectName:"connectionAction"
                        label:root.wifi ? (root.selected && root.selected.connected ? "Desconectar":"Conectar") : (root.selected && root.selected.connected ? "Desconectar":root.selected && root.selected.paired?"Conectar":"Parear e conectar")
                        enabled:!!root.state.enabled && !ConnectivityState.busy && !ControlCenterState.state.airplaneManaged
                        emphasized:true
                        onClicked: {
                            const item=root.selected;if (!item) return;
                            const name=root.wifi ? (item.connected?"wifi-disconnect":"wifi-connect") : item.connected?"blue-disconnect":item.paired?"blue-connect":"blue-pair";
                            const value={id:item.id};if (name==="wifi-connect") { value.password=password.text;value.save=save.checked; }
                            ConnectivityState.action(name,value);password.text="";root.selected=null;
                        }
                    }
                    ThemeButton { visible:root.wifi ? !!root.selected && root.selected.saved : !!root.selected && root.selected.paired;label:"Esquecer";enabled:!ConnectivityState.busy;onClicked:root.confirmation="forget" }
                    ThemeButton { visible:!root.wifi;label:root.selected && root.selected.trusted ? "Não confiar":"Confiar";enabled:!ConnectivityState.busy;onClicked: { ConnectivityState.action("blue-trust",{id:root.selected.id,enabled:!root.selected.trusted});root.selected=null; } }
                    ThemeButton { visible:!root.wifi;label:root.selected && root.selected.blocked ? "Desbloquear":"Bloquear";enabled:!ConnectivityState.busy;onClicked: { ConnectivityState.action("blue-block",{id:root.selected.id,enabled:!root.selected.blocked});root.selected=null; } }
                }
                Column {
                    width:parent.width;spacing:8;visible:root.confirmation!==""
                    Text { width:parent.width;text:"Esquecer a conexão/pareamento? Isso pode desconectar o dispositivo.";color:Theme.warning;font.family:Theme.fontFamily;font.pixelSize:11;wrapMode:Text.WordWrap }
                    Row { spacing:8;ThemeButton { label:"Confirmar";onClicked: { ConnectivityState.action(root.wifi?"wifi-forget":"blue-forget",{id:root.selected.id,confirmed:true});root.reset(); } } ThemeButton { label:"Cancelar";onClicked:root.confirmation="" } }
                }
            }
            Column {
                width:parent.width;spacing:10;visible:!!ConnectivityState.challenge.kind
                Text { width:parent.width;text:(ConnectivityState.challenge.device || "Bluetooth")+" · "+(ConnectivityState.challenge.code || "Confirme ou digite o código do dispositivo.");color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:14;wrapMode:Text.WordWrap;textFormat:Text.PlainText }
                TextField {
                    id:pin;width:parent.width;visible:["pin","passkey"].includes(ConnectivityState.challenge.kind)
                    placeholderText:"PIN / código de pareamento";maximumLength:16;color:Theme.text;placeholderTextColor:Theme.secondaryText;font.family:Theme.fontFamily
                    background:Rectangle { radius:10;color:Theme.elevatedSurface;border.color:Theme.border }
                }
                Row {
                    spacing:8
                    ThemeButton { label:"Confirmar";visible:ConnectivityState.challenge.kind!=="display";onClicked: { ConnectivityState.action("answer",{id:ConnectivityState.challenge.id,accept:true,value:pin.text});pin.text=""; } }
                    ThemeButton { label:"Cancelar";onClicked: { ConnectivityState.action("cancel-pair");pin.text=""; } }
                }
            }
        }
    }
}
