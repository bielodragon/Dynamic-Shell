pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    readonly property var sources: Object.assign({steam:true,localsend:true,minecraft:true,terminal:true,editors:true},ThemeStore.config.integrations || {})
    readonly property bool enabled: Preferences.enabled("activities") && Object.keys(sources).some(key => sources[key])
    property var owned: []
    property var seen: ({})
    property string message: ""
    function clear() { for (const id of owned) ActivityState.remove(id); owned=[];seen=({}); }
    function receive(rows) {
        const ids=rows.map(row=>row.id),now=Date.now();
        for (const id of owned) if (!ids.includes(id)) { ActivityState.remove(id);delete seen[id]; }
        for (const row of rows) {
            const signature=JSON.stringify({title:row.title,detail:row.detail,state:row.state,progress:row.progress});
            const previous=seen[row.id];
            if (!previous || previous.signature!==signature || now-previous.at>6000) {
                try { ActivityState.update(row);seen[row.id]={signature:signature,at:now}; }
                catch (error) { message=String(error); }
            }
        }
        owned=ids;
    }
    onEnabledChanged: {
        observer.running=enabled;
        if (!enabled) { restart.stop();clear(); }
    }
    Process {
        id: observer
        command: ["python3",Quickshell.shellPath("scripts/app_integrations.py"),"monitor",JSON.stringify(root.sources)]
        running: root.enabled
        onCommandChanged: if (running) { running=false;restart.restart(); }
        stdout: SplitParser { onRead: line=> { try { root.receive(JSON.parse(line).activities || []); } catch (_) { root.message="Não foi possível ler as atividades de apps."; } } }
        onExited: { root.clear();if (root.enabled) restart.restart(); }
    }
    Timer { id:restart;interval:1500;onTriggered:if (root.enabled) observer.running=true }
    IpcHandler {
        target:"app-integrations"
        function status(): string { return JSON.stringify({enabled:root.enabled,sources:root.sources,activities:root.owned,message:root.message}); }
    }
}
