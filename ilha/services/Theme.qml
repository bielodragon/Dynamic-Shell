pragma Singleton
import QtQuick
import Quickshell

Singleton {
    readonly property color transparent: "#00000000"
    // Tokens semânticos. Só este serviço recebe valores dos arquivos JSON.
    property color background: "#111216"
    property color surface: "#1a1b20"
    property color elevatedSurface: "#24262d"
    property color text: "#f2f2f4"
    property color secondaryText: "#afb0b8"
    property color accent: "#aeb9ff"
    property color border: "#40414a"
    property color success: "#88d8a2"
    property color error: "#ff9b9b"
    property color warning: "#ffd18a"
    property real glassOpacity: 0.94
    property real blurIntensity: 0.0
    // O raio do blur pertence ao compositor; este token controla quanto
    // do fundo desfocado fica visível através da superfície.
    readonly property real effectiveGlassOpacity: Math.max(0, Math.min(1, glassOpacity * (1 - 0.35 * blurIntensity)))
    readonly property int morphDuration: Math.round(260 * Preferences.animationScale)
    readonly property int contentDuration: Math.round(180 * Preferences.animationScale)
    readonly property int colorDuration: Math.round(230 * Preferences.animationScale)
    readonly property string fontFamily: "JetBrainsMono Nerd Font"

    function apply(theme, overrides) {
        if (!theme || !theme.colors) return;
        const colors = theme.colors;
        background = colors.background;
        surface = colors.surface;
        elevatedSurface = colors.elevatedSurface;
        text = colors.text;
        secondaryText = colors.secondaryText;
        accent = overrides && overrides.accent !== null && overrides.accent !== undefined ? overrides.accent : colors.accent;
        border = colors.border;
        success = colors.success;
        error = colors.error;
        warning = colors.warning;
        // OLED permanece sólido mesmo quando há ajustes globais de vidro.
        glassOpacity = theme.id === "oled" ? 1 : (overrides && overrides.glassOpacity !== null && overrides.glassOpacity !== undefined ? overrides.glassOpacity : theme.glassOpacity);
        blurIntensity = theme.id === "oled" ? 0 : (overrides && overrides.blurIntensity !== null && overrides.blurIntensity !== undefined ? overrides.blurIntensity : theme.blurIntensity);
    }

    Behavior on background { ColorAnimation { duration: colorDuration } }
    Behavior on surface { ColorAnimation { duration: colorDuration } }
    Behavior on elevatedSurface { ColorAnimation { duration: colorDuration } }
    Behavior on text { ColorAnimation { duration: colorDuration } }
    Behavior on secondaryText { ColorAnimation { duration: colorDuration } }
    Behavior on accent { ColorAnimation { duration: colorDuration } }
    Behavior on border { ColorAnimation { duration: colorDuration } }
    Behavior on success { ColorAnimation { duration: colorDuration } }
    Behavior on error { ColorAnimation { duration: colorDuration } }
    Behavior on warning { ColorAnimation { duration: colorDuration } }
    Behavior on glassOpacity { NumberAnimation { duration: colorDuration } }
}
