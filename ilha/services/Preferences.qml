pragma Singleton
import QtQuick
import Quickshell
import qs.services

Singleton {
    readonly property var modules: ThemeStore.config.modules || ({})
    readonly property bool animationsEnabled: !ThemeStore.config.animations || ThemeStore.config.animations.enabled !== false
    readonly property real animationScale: animationsEnabled ? (ThemeStore.config.animations ? ThemeStore.config.animations.scale || 1 : 1) : 0
    function enabled(name) { return modules[name] !== false; }
    function setModule(name, value) { const update = {}; update[name] = value; ThemeStore.setPreferences({ modules: update }); }
}
