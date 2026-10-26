import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import Quickshell
import qs.components
import qs.services
import "../components/ColorUtils.js" as Colors

Item {
    id: root
    signal closeRequested()
    implicitWidth: 880
    implicitHeight: 820
    readonly property var tokenNames: [
        { key: "background", label: "Fundo" }, { key: "surface", label: "Superfície" },
        { key: "elevatedSurface", label: "Superfície elevada" }, { key: "text", label: "Texto" },
        { key: "secondaryText", label: "Texto secundário" }, { key: "accent", label: "Destaque" },
        { key: "border", label: "Borda" }, { key: "success", label: "Sucesso" },
        { key: "error", label: "Erro" }, { key: "warning", label: "Aviso" }
    ]
    property var draft: null
    property string draftId: ""
    property string chosenToken: "background"
    property string dialogPrevious: ""
    property real hue: 0
    property real saturation: 0
    property real value: 0
    property real localGlass: 1
    property real localBlur: 0
    property string localAccent: ""
    property bool confirmDelete: false
    readonly property real contrastRatio: draft ? Colors.contrast(draft.colors.text, draft.colors.background) : 21

    function chooseToken(token) {
        chosenToken = token;
        if (!draft) return;
        const hsv = Colors.rgbToHsv(draft.colors[token]);
        hue = hsv[0]; saturation = hsv[1]; value = hsv[2];
    }

    function loadDraft(theme) {
        if (!theme) return;
        draft = JSON.parse(JSON.stringify(theme));
        draftId = theme.builtin ? "" : theme.id;
        confirmDelete = false;
        themeName.text = theme.builtin ? theme.name + " — meu tema" : theme.name;
        chooseToken(chosenToken);
        const overrides = ThemeStore.config.overrides || {};
        localGlass = overrides.glassOpacity !== null && overrides.glassOpacity !== undefined ? overrides.glassOpacity : theme.glassOpacity;
        localBlur = overrides.blurIntensity !== null && overrides.blurIntensity !== undefined ? overrides.blurIntensity : theme.blurIntensity;
        localAccent = overrides.accent || "";
    }

    function setColor(token, hex) {
        if (!draft || !/^#[0-9a-fA-F]{6}$/.test(hex)) return false;
        const copy = JSON.parse(JSON.stringify(draft));
        copy.colors[token] = hex.toLowerCase();
        draft = copy;
        ThemeStore.preview(draft);
        return true;
    }

    function previewOverrides() {
        if (!draft) return;
        Theme.apply(draft, { accent: localAccent || null, glassOpacity: localGlass, blurIntensity: localBlur });
    }

    function saveDraft() {
        if (!draft) return;
        const copy = JSON.parse(JSON.stringify(draft));
        copy.name = themeName.text.trim();
        ThemeStore.save(copy, draftId);
    }

    Component.onCompleted: loadDraft(ThemeStore.selectedTheme)
    Component.onDestruction: ThemeStore.restore()

    Connections {
        target: ThemeStore
        function onReadyChanged() { if (ThemeStore.ready && !root.draft) root.loadDraft(ThemeStore.selectedTheme); }
        function onOperationFinished(operation, ok) {
            if (ok && ["select", "save", "duplicate", "delete", "import"].includes(operation)) root.loadDraft(ThemeStore.selectedTheme);
            if (ok && operation === "overrides") root.previewOverrides();
        }
    }

    ColorDialog {
        id: colorDialog
        title: "Escolher cor"
        onSelectedColorChanged: if (visible && root.draft) root.setColor(root.chosenToken, Colors.qcolorToHex(selectedColor))
        onRejected: root.setColor(root.chosenToken, root.dialogPrevious)
        onAccepted: root.chooseToken(root.chosenToken)
    }

    Rectangle {
        id: board
        anchors.fill: parent
        radius: 24
        color: Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, Theme.effectiveGlassOpacity)
        border.color: Theme.border
        border.width: 1

        Text {
            x: 24; y: 20
            text: "Temas da ilha"
            color: Theme.text
            font.family: Theme.fontFamily
            font.pixelSize: 20
            font.weight: Font.DemiBold
        }
        ThemeButton {
            anchors.right: parent.right
            anchors.rightMargin: 22
            y: 17
            label: "Fechar ✕"
            onClicked: root.closeRequested()
        }

        Rectangle {
            x: 22; y: 61; width: parent.width - 44; height: 1
            color: Theme.border
        }

        Column {
            x: 24; y: 78; width: 302; spacing: 11
            Text {
                text: "Escolha com um clique"
                color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13
            }
            Flickable {
                width: 302; height: board.height - 208
                clip: true
                contentHeight: cardGrid.height
                boundsBehavior: Flickable.StopAtBounds

                Grid {
                    id: cardGrid
                    columns: 2; spacing: 10
                    Repeater {
                        model: ThemeStore.themes
                        Rectangle {
                            id: card
                            required property var modelData
                            readonly property var themeData: modelData
                            width: 144; height: 102; radius: 14
                            color: themeData.colors.surface
                            border.color: ThemeStore.config.theme === themeData.id ? Theme.accent : themeData.colors.border
                            border.width: ThemeStore.config.theme === themeData.id ? 2 : 1

                            Rectangle { x: 10; y: 10; width: 84; height: 22; radius: 11; color: card.themeData.colors.background }
                            Text { x: 17; y: 13; text: "15:08"; color: card.themeData.colors.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                            Row {
                                x: 10; y: 40; spacing: 5
                                Repeater {
                                    model: ["accent", "surface", "text", "success", "error"]
                                    Rectangle { required property string modelData; width: 16; height: 16; radius: 8; color: card.themeData.colors[modelData]; border.color: card.themeData.colors.border }
                                }
                            }
                            Text {
                                x: 10; y: 70; width: 126
                                text: card.themeData.name
                                elide: Text.ElideRight
                                color: card.themeData.colors.text
                                font.family: Theme.fontFamily; font.pixelSize: 10
                            }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: { root.loadDraft(card.themeData); ThemeStore.preview(card.themeData); ThemeStore.select(card.themeData.id); }
                            }
                        }
                    }
                }
            }
            Row {
                spacing: 8
                ThemeButton { label: "Duplicar"; enabled: !!ThemeStore.selectedTheme; onClicked: ThemeStore.duplicate(ThemeStore.config.theme) }
                ThemeButton {
                    label: root.confirmDelete ? "Confirmar exclusão" : "Apagar"
                    enabled: ThemeStore.selectedTheme && !ThemeStore.selectedTheme.builtin
                    onClicked: {
                        if (root.confirmDelete) ThemeStore.remove(ThemeStore.config.theme);
                        else root.confirmDelete = true;
                    }
                }
            }
        }

        Rectangle { x: 339; y: 76; width: 1; height: board.height - 134; color: Theme.border }

        Flickable {
            x: 358; y: 78; width: board.width - 378; height: board.height - 128
            clip: true
            contentHeight: editor.height
            boundsBehavior: Flickable.StopAtBounds

            Column {
                id: editor
                width: 478
                spacing: 12

                Text { text: "Editar cores"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 16; font.weight: Font.DemiBold }
                ThemePreview { }
                Text { text: "Prévia ao vivo antes de salvar"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }

                TextField {
                    id: themeName
                    width: 452; height: 34
                    placeholderText: "Nome do meu tema"
                    color: Theme.text; placeholderTextColor: Theme.secondaryText
                    font.family: Theme.fontFamily; font.pixelSize: 12
                    background: Rectangle { color: Theme.elevatedSurface; radius: 9; border.color: Theme.border }
                }

                Column {
                    spacing: 5
                    Repeater {
                        model: root.tokenNames
                        Rectangle {
                            id: tokenRow
                            required property var modelData
                            readonly property string token: modelData.key
                            width: 452; height: 35; radius: 8
                            color: root.chosenToken === token ? Theme.elevatedSurface : Theme.surface

                            Text { x: 9; anchors.verticalCenter: parent.verticalCenter; text: tokenRow.modelData.label; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                            Rectangle {
                                x: 265; anchors.verticalCenter: parent.verticalCenter
                                width: 22; height: 22; radius: 6
                                color: root.draft ? root.draft.colors[tokenRow.token] : Theme.background
                                border.color: Theme.border
                                MouseArea {
                                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.chooseToken(tokenRow.token);
                                        root.dialogPrevious = root.draft.colors[tokenRow.token];
                                        colorDialog.selectedColor = root.dialogPrevious;
                                        colorDialog.open();
                                    }
                                }
                            }
                            TextField {
                                x: 295; width: 148; height: 30
                                anchors.verticalCenter: parent.verticalCenter
                                text: root.draft ? root.draft.colors[tokenRow.token] : ""
                                color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11
                                selectByMouse: true
                                background: Rectangle { color: Theme.background; radius: 7; border.color: Theme.border }
                                onTextEdited: if (/^#[0-9a-fA-F]{6}$/.test(text)) { root.setColor(tokenRow.token, text); root.chooseToken(tokenRow.token); }
                                onEditingFinished: { if (!/^#[0-9a-fA-F]{6}$/.test(text)) text = root.draft.colors[tokenRow.token]; }
                            }
                        }
                    }
                }

                Text { text: "HSV — " + root.tokenNames.find(item => item.key === root.chosenToken).label; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 12 }
                Row {
                    spacing: 8
                    Repeater {
                        model: [{ label: "H", maximum: 359 }, { label: "S", maximum: 100 }, { label: "V", maximum: 100 }]
                        Column {
                            id: hsvColumn
                            required property var modelData
                            spacing: 3
                            Text { text: hsvColumn.modelData.label; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 10 }
                            Slider {
                                width: 143; height: 25
                                from: 0; to: hsvColumn.modelData.maximum
                                value: hsvColumn.modelData.label === "H" ? root.hue : hsvColumn.modelData.label === "S" ? root.saturation * 100 : root.value * 100
                                background: Rectangle { x: 0; y: 10; width: parent.width; height: 5; radius: 3; color: Theme.elevatedSurface }
                                handle: Rectangle { x: parent.visualPosition * (parent.width - width); y: 3; width: 17; height: 17; radius: 9; color: Theme.accent }
                                onMoved: {
                                    if (hsvColumn.modelData.label === "H") root.hue = value;
                                    else if (hsvColumn.modelData.label === "S") root.saturation = value / 100;
                                    else root.value = value / 100;
                                    root.setColor(root.chosenToken, Colors.hsvToHex(root.hue, root.saturation, root.value));
                                }
                            }
                        }
                    }
                }

                Text {
                    visible: root.contrastRatio < 4.5
                    text: "⚠ Contraste texto/fundo: " + root.contrastRatio.toFixed(2) + ":1 (referência WCAG: 4,5:1)"
                    color: Theme.warning; font.family: Theme.fontFamily; font.pixelSize: 11
                }
                Row {
                    spacing: 8
                    ThemeButton { label: "Salvar tema"; emphasized: true; onClicked: root.saveDraft() }
                    ThemeButton { label: "Descartar prévia"; onClicked: { root.loadDraft(ThemeStore.selectedTheme); ThemeStore.restore(); } }
                }

                Rectangle { width: 452; height: 1; color: Theme.border }
                Text { text: "Ajustes separados do tema"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13 }
                Row {
                    spacing: 8
                    Text { width: 120; anchors.verticalCenter: parent.verticalCenter; text: "Destaque global"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    TextField {
                        width: 160; height: 32
                        text: root.localAccent
                        placeholderText: "cor do tema"
                        color: Theme.text; placeholderTextColor: Theme.secondaryText
                        font.family: Theme.fontFamily; font.pixelSize: 11
                        background: Rectangle { color: Theme.elevatedSurface; radius: 8; border.color: Theme.border }
                        onTextEdited: if (/^#[0-9a-fA-F]{6}$/.test(text)) { root.localAccent = text; root.previewOverrides(); }
                        onEditingFinished: if (text === "" || /^#[0-9a-fA-F]{6}$/.test(text)) { root.localAccent = text; ThemeStore.setOverrides({ accent: text || null }); }
                    }
                    ThemeButton { label: "Usar tema"; onClicked: { root.localAccent = ""; root.previewOverrides(); ThemeStore.setOverrides({ accent: null }); } }
                }
                Row {
                    spacing: 8
                    Text { width: 120; anchors.verticalCenter: parent.verticalCenter; text: "Opacidade"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider {
                        width: 250; from: 0.55; to: 1; value: root.localGlass
                        onMoved: { root.localGlass = value; root.previewOverrides(); }
                        onPressedChanged: if (!pressed) ThemeStore.setOverrides({ glassOpacity: root.localGlass })
                    }
                    Text { text: Math.round(root.localGlass * 100) + "%"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                }
                Row {
                    spacing: 8
                    Text { width: 120; anchors.verticalCenter: parent.verticalCenter; text: "Intensidade blur"; color: Theme.secondaryText; font.family: Theme.fontFamily; font.pixelSize: 11 }
                    ThemeSlider {
                        width: 250; from: 0; to: 1; value: root.localBlur
                        onMoved: root.localBlur = value
                        onPressedChanged: if (!pressed) ThemeStore.setOverrides({ blurIntensity: root.localBlur })
                    }
                    Text { text: Math.round(root.localBlur * 100) + "%"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 11 }
                }

                Rectangle { width: 452; height: 1; color: Theme.border }
                Text { text: "Compartilhar JSON"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: 13 }
                TextField {
                    id: jsonPath
                    width: 452; height: 34
                    placeholderText: "/home/usuario/Downloads/meu-tema.json"
                    color: Theme.text; placeholderTextColor: Theme.secondaryText
                    font.family: Theme.fontFamily; font.pixelSize: 11
                    background: Rectangle { color: Theme.elevatedSurface; radius: 8; border.color: Theme.border }
                }
                Row {
                    spacing: 8
                    ThemeButton { label: "Importar"; onClicked: ThemeStore.importFile(jsonPath.text) }
                    ThemeButton { label: "Exportar selecionado"; onClicked: ThemeStore.exportFile(ThemeStore.config.theme, jsonPath.text) }
                }
                Text {
                    width: 450; wrapMode: Text.Wrap
                    text: ThemeStore.message
                    visible: text.length > 0
                    color: ThemeStore.messageIsError ? Theme.error : Theme.success; font.family: Theme.fontFamily; font.pixelSize: 11
                }
                Item { width: 1; height: 16 }
            }
        }
    }
}
