import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Widgets
import qs.services

Item {
    id: root
    required property var targetScreen
    required property bool expanded
    property bool activityCompact: false
    property string style: "icons"
    property int maxVisible: 6
    property int overflowCount: 0
    property int contentWidth: 0
    signal workspaceActivated(string name)

    readonly property var targetMonitor: targetScreen ? Hyprland.monitorFor(targetScreen) : null
    readonly property var activeWorkspace: targetMonitor && Hyprland.focusedMonitor
        && Hyprland.focusedMonitor.name === targetMonitor.name && Hyprland.focusedWorkspace
        ? Hyprland.focusedWorkspace : (targetMonitor ? targetMonitor.activeWorkspace : null)
    readonly property int activeWorkspaceId: activeWorkspace ? activeWorkspace.id
        : (targetMonitor && targetMonitor.lastIpcObject && targetMonitor.lastIpcObject.activeWorkspace
            ? targetMonitor.lastIpcObject.activeWorkspace.id : -1)
    readonly property bool useDots: style === "dots" || (activityCompact && !expanded)
    width: contentWidth + (overflowCount > 0 ? 31 : 0)
    height: expanded ? 26 : 22
    Behavior on width { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }

    function iconFor(workspace) {
        const windows = workspace.toplevels.values;
        if (!windows || windows.length === 0) return "";
        const main = windows.find(window => window.activated) || windows[0];
        const ipc = main.lastIpcObject || {};
        const appClass = ipc.class || ipc.initialClass || "";
        const entry = appClass ? DesktopEntries.heuristicLookup(appClass) : null;
        return entry && entry.icon ? Quickshell.iconPath(entry.icon, true)
            : (appClass ? Quickshell.iconPath(appClass.toLowerCase(), true) : "");
    }

    function rows() {
        const monitor = targetMonitor;
        if (!monitor) return [];
        const result = [];
        for (const workspace of Hyprland.workspaces.values) {
            const ipc = workspace.lastIpcObject || {};
            const onMonitor = (workspace.monitor && workspace.monitor.name === monitor.name)
                || ipc.monitor === monitor.name || workspace.id === activeWorkspaceId;
            if (!onMonitor) continue;
            const count = Math.max(workspace.toplevels.values.length, Number(ipc.windows || 0));
            if (count === 0 && workspace.id !== activeWorkspaceId) continue;
            result.push({ workspaceId: workspace.id, workspaceName: workspace.name,
                windowCount: count, appIcon: iconFor(workspace), selected: workspace.id === activeWorkspaceId });
        }
        if (activeWorkspace && !result.some(item => item.workspaceId === activeWorkspaceId))
            result.push({ workspaceId: activeWorkspaceId, workspaceName: activeWorkspace.name,
                windowCount: 0, appIcon: "", selected: true });
        result.sort((a, b) => a.workspaceId - b.workspaceId);
        return result;
    }

    function synchronize() {
        const all = rows();
        const limit = Math.max(2, maxVisible);
        let shown = all.slice(0, limit);
        if (!shown.some(item => item.selected) && all.some(item => item.selected)) {
            shown[shown.length - 1] = all.find(item => item.selected);
            shown.sort((a, b) => a.workspaceId - b.workspaceId);
        }
        overflowCount = all.length - shown.length;
        for (let i = workspaceModel.count - 1; i >= 0; --i)
            if (!shown.some(item => item.workspaceId === workspaceModel.get(i).workspaceId))
                workspaceModel.setProperty(i, "present", false);
        for (let i = 0; i < shown.length; ++i) {
            shown[i].present = true;
            let existing = -1;
            for (let j = 0; j < workspaceModel.count; ++j)
                if (workspaceModel.get(j).workspaceId === shown[i].workspaceId) { existing = j; break; }
            if (existing < 0) {
                if (i >= workspaceModel.count) workspaceModel.append(shown[i]);
                else workspaceModel.insert(i, shown[i]);
            }
            else {
                // Reposiciona por reinserção; move() em ListModel 6.10 pode
                // rejeitar um destino durante atualizações simultâneas do IPC.
                if (existing !== i) {
                    workspaceModel.remove(existing);
                    if (i >= workspaceModel.count) workspaceModel.append(shown[i]);
                    else workspaceModel.insert(i, shown[i]);
                } else workspaceModel.set(i, shown[i]);
            }
        }
        updateWidth();
        if (workspaceModel.count > shown.length) removeDelay.restart();
    }

    function itemWidth(selected) {
        if (useDots) return selected ? (expanded ? 26 : 18) : (expanded ? 14 : 8);
        return selected ? (expanded ? 53 : 43) : (expanded ? 42 : 34);
    }

    function updateWidth() {
        let total = 0;
        for (let i = 0; i < workspaceModel.count; ++i)
            total += (i ? 5 : 0) + (workspaceModel.get(i).present ? itemWidth(workspaceModel.get(i).selected) : 0);
        contentWidth = total;
    }

    function activateWorkspace(id, name) {
        // O Hyprland instalado usa Lua; enviamos o nome como string escapada.
        if (Hyprland.usingLua)
            Quickshell.execDetached(["hyprctl", "eval", "hl.dispatch(hl.dsp.focus({workspace=" + JSON.stringify(name) + "}))"]);
        else Hyprland.dispatch("workspace " + name);
        workspaceActivated(name);
    }

    function step(direction) {
        if (!Preferences.enabled("workspaces")) return;
        const all = rows();
        if (all.length < 2) return;
        let index = all.findIndex(item => item.selected);
        if (index < 0) index = 0;
        const next = all[(index + direction + all.length) % all.length];
        activateWorkspace(next.workspaceId, next.workspaceName);
    }

    onActiveWorkspaceIdChanged: synchronize()
    onTargetMonitorChanged: synchronize()
    onExpandedChanged: updateWidth()
    onUseDotsChanged: updateWidth()
    onMaxVisibleChanged: synchronize()
    Component.onCompleted: {
        Hyprland.refreshWorkspaces();
        Hyprland.refreshToplevels();
        refreshDelay.restart();
    }

    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["openwindow", "closewindow", "movewindow", "movewindowv2",
                 "createworkspace", "destroyworkspace", "workspace", "workspacev2",
                 "focusedmon", "monitoradded", "monitorremoved"].includes(event.name))
                refreshDelay.restart();
        }
        function onFocusedWorkspaceChanged() { root.synchronize(); }
        function onFocusedMonitorChanged() { root.synchronize(); }
    }
    Timer {
        id: refreshDelay
        interval: 120
        onTriggered: {
            Hyprland.refreshWorkspaces();
            Hyprland.refreshToplevels();
            settleDelay.restart();
        }
    }
    Timer { id: settleDelay; interval: 120; onTriggered: root.synchronize() }
    Timer {
        id: removeDelay
        interval: Theme.contentDuration + 30
        onTriggered: {
            for (let i = workspaceModel.count - 1; i >= 0; --i)
                if (!workspaceModel.get(i).present) workspaceModel.remove(i);
            root.updateWidth();
        }
    }
    ListModel { id: workspaceModel }

    Row {
        anchors.verticalCenter: parent.verticalCenter
        spacing: 5
        Repeater {
            model: workspaceModel
            Rectangle {
                id: badge
                required property int workspaceId
                required property string workspaceName
                required property int windowCount
                required property string appIcon
                required property bool selected
                required property bool present
                width: present ? root.itemWidth(selected) : 0
                height: present ? (root.useDots ? (selected ? 13 : 8) : (root.expanded ? 25 : 21)) : 0
                radius: height / 2
                color: selected ? Theme.accent : Theme.elevatedSurface
                border.color: selected ? Theme.accent : Theme.border
                border.width: 1
                opacity: !present ? 0 : selected ? 1 : 0.84
                scale: 1
                Behavior on width { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }
                Behavior on height { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: Theme.contentDuration } }
                Behavior on color { ColorAnimation { duration: Theme.contentDuration } }
                Behavior on x { NumberAnimation { duration: Theme.contentDuration; easing.type: Easing.OutCubic } }
                Component.onCompleted: enter.start()
                SequentialAnimation {
                    id: enter
                    PropertyAction { target: badge; property: "scale"; value: 0.25 }
                    PropertyAction { target: badge; property: "opacity"; value: 0 }
                    ParallelAnimation {
                        NumberAnimation { target: badge; property: "scale"; to: 1; duration: Theme.contentDuration; easing.type: Easing.OutBack }
                        NumberAnimation { target: badge; property: "opacity"; to: badge.selected ? 1 : 0.84; duration: Theme.contentDuration }
                    }
                }
                IconImage {
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    width: 14; height: 14
                    source: badge.appIcon
                    visible: !root.useDots && badge.appIcon !== ""
                }
                Text {
                    anchors.centerIn: parent
                    text: badge.workspaceName
                    visible: !root.useDots && badge.appIcon === ""
                    color: badge.selected ? Theme.background : Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }
                Text {
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    text: badge.windowCount > 1 ? String(badge.windowCount) : (badge.appIcon !== "" ? badge.workspaceName : "")
                    visible: !root.useDots && (badge.windowCount > 1 || badge.appIcon !== "")
                    color: badge.selected ? Theme.background : Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: 9
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.activateWorkspace(badge.workspaceId, badge.workspaceName)
                }
            }
        }
        Rectangle {
            visible: root.overflowCount > 0
            width: visible ? 26 : 0
            height: root.useDots ? 14 : 22
            radius: height / 2
            color: Theme.elevatedSurface
            Text {
                anchors.centerIn: parent
                text: "+" + root.overflowCount
                color: Theme.secondaryText
                font.family: Theme.fontFamily
                font.pixelSize: 9
            }
        }
    }
}
