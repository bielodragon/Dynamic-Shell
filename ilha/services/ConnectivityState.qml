pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    property string mode: ""
    property var state: ({})
    property var challenge: ({})
    property bool busy: false
    property string message: ""
    property bool ready: false
    readonly property bool visible: ControlCenterState.opened && mode !== ""
    function open(value) { state=({});message="";challenge=({});mode=value;if (ready) send({action:"mode",mode:value}); }
    function close() { mode="";challenge=({});state=({});message="";busy=false;ready=false; }
    function send(payload) {
        if (!worker.running || !ready) return;
        worker.write(JSON.stringify(payload)+"\n");
    }
    function action(name,payload) { message="";send(Object.assign({action:name},payload || {})); }
    Connections { target:ControlCenterState; function onOpenedChanged() { if (!ControlCenterState.opened) root.close(); } }
    Process {
        id: worker
        command:["python3",Quickshell.shellPath("scripts/connectivity_service.py")]
        running:root.visible
        stdinEnabled:true
        stdout:SplitParser {
            onRead:line=>{
                try {
                    const value=JSON.parse(line);
                    if (!root.visible) return;
                    if (!root.ready) { root.ready=true;root.send({action:"mode",mode:root.mode}); }
                    if (value.type==="state" && value.mode===root.mode) { root.state=value.state;root.busy=value.busy;root.message=value.message; }
                    else if (value.type==="challenge") root.challenge=value;
                    else if (value.type==="error") { root.message=value.message; }
                } catch (_) { root.message="Não foi possível ler os dispositivos."; }
            }
        }
        onExited: { root.ready=false;root.busy=false;if (root.visible) root.message="O serviço de conectividade foi encerrado. Volte e abra o painel novamente."; }
    }
    IpcHandler {
        target:"connectivity"
        function open(mode:string):void { if (["wifi","bluetooth"].includes(mode) && ControlCenterState.opened) root.open(mode); }
        function back():void { root.close(); }
        function status():string { return JSON.stringify({mode:root.mode,ready:root.ready,busy:root.busy,state:root.state,message:root.message}); }
    }
}
