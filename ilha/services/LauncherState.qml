pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import "../components/LauncherSearch.js" as Search

Singleton {
    id: root
    readonly property bool enabled: Preferences.enabled("launcher")
    property bool opened: false
    property bool closing: false
    readonly property bool present: opened || closing
    property string screenName: ""
    property real originWidth: 220
    property real originHeight: 36
    property real originRadius: 18
    property string query: ""
    readonly property string mode: query.startsWith("=") ? "calculator" : query.startsWith(":") ? "clipboard" : query.startsWith(">") ? "commands" : "apps"
    property var results: []
    onResultsChanged: selectedIndex = Math.max(0, Math.min(selectedIndex, results.length - 1))
    property var clipboardRows: []
    property var wallpaperRows: [] // Miniaturas consultadas sob demanda ao entrar no seletor.
    property var integrationRows: []
    property string integrationSource: ""
    property bool selectingTheme: false
    readonly property string commandBody: query.slice(1).replace(/^\s+/, "")
    readonly property string commandSection: /^(wallpaper|wallpapers|papel)\s/i.test(commandBody) ? "wallpapers"
        : /^(scheme|schema|temas|theme)\s/i.test(commandBody) ? "themes"
        : /^(steam|jogos)\s/i.test(commandBody) ? "steam"
        : /^(minecraft|mine|prism)\s/i.test(commandBody) ? "minecraft"
        : /^localsend\s/i.test(commandBody) ? "localsend" : "actions"
    readonly property string commandFilter: commandBody.replace(/^\S+\s+/, "")
    property int selectedIndex: 0
    property string message: ""
    property bool actionBusy: false
    property bool readBusy: false
    property bool readReceived: false
    property var pendingRead: null
    property var reading: null
    readonly property var applications: DesktopEntries.applications.values
    onEnabledChanged: if (!enabled) close()
    onApplicationsChanged: if (opened && mode === "apps") rebuild()
    // Aguardar as bindings de mode antes de decidir qual fonte consultar.
    onQueryChanged: { selectedIndex = 0; message = ""; Qt.callLater(root.rebuild); }

    function open(name, width, height, radius) {
        if (!enabled) return;
        const target = name ? Array.from(Quickshell.screens).find(screen => screen.name === name) : Quickshell.screens[0];
        if (!target) { message = "Monitor indisponível."; return; }
        closeFallback.stop();
        screenName = target.name;
        originWidth = width || 220; originHeight = height || 36; originRadius = radius || 18;
        ControlCenterState.close(); SettingsState.opened = false;
        closing = false; opened = true; query = ""; selectedIndex = 0; rebuild();
    }
    function close() {
        if (!present) return;
        closing = true; opened = false; pendingRead = null;
        debounce.stop();
        closeFallback.restart();
    }
    function finishClose() {
        if (!opened) { closing = false; query = ""; clipboardRows = []; results = []; closeFallback.stop(); }
    }
    function setMode(value) { query = ({apps:"",calculator:"= ",clipboard:": ",commands:"> "})[value] || ""; }
    function openWallpapers(name) { if (enabled) { open(name); query = "> wallpaper "; } }
    function move(delta) { if (results.length) selectedIndex = (selectedIndex + delta + results.length) % results.length; }
    function rebuild() {
        if (!opened) return;
        if (mode !== "clipboard") clipboardRows = [];
        if (mode === "apps") results = Search.apps(applications, query);
        else if (mode === "commands") {
            if (commandSection === "wallpapers") {
                results = Search.filterRows(wallpaperRows, commandFilter);
                debounce.restart();
            } else if (commandSection === "themes") {
                results = Search.filterRows(ThemeStore.themes.map(theme => ({kind:"theme",id:theme.id,
                    title:theme.name,detail:theme.builtin ? "Tema pronto" : "Tema personalizado",
                    icon:"preferences-desktop-theme",swatches:[theme.colors.background,theme.colors.text,theme.colors.accent]})), commandFilter);
            } else if (["steam","localsend","minecraft"].includes(commandSection)) {
                results=integrationSource===commandSection ? Search.filterRows(integrationRows,commandFilter) : [];
                debounce.restart();
            } else {
                results = Search.actions(commandBody.trim());
                if (!results.length && commandBody.trim()) results = [{kind:"command",title:commandBody.trim(),detail:"Executar no terminal",icon:"utilities-terminal"}];
            }
        }
        else if (mode === "clipboard") { results = Search.clipboard(clipboardRows, query.slice(1)); debounce.restart(); }
        else { results = []; debounce.restart(); }
    }
    function requestRead(operation, payload) { pendingRead = {operation, payload, query}; startRead(); }
    function startRead() {
        if (readBusy || !pendingRead || !opened) return;
        reading = pendingRead; pendingRead = null; readBusy = true; readReceived = false;
        reader.exec(["python3", Quickshell.shellPath("scripts/launcher_backend.py"), reading.operation, JSON.stringify(reading.payload)]);
    }
    function finishRead() { if (!readReceived) return; readBusy = false; reading = null; startRead(); }
    function activate(index) {
        const item = results[index === undefined ? selectedIndex : index];
        if (!opened || !item || actionBusy) return;
        if (item.kind === "action") {
            if (item.id === "wallpapers") { wallpaperRows = []; query = "> wallpaper "; return; }
            if (item.id === "themes") { query = "> scheme "; return; }
            if (["steam","localsend","minecraft"].includes(item.id)) { integrationRows=[];integrationSource="";query="> "+item.id+" ";return; }
            if (item.id === "light" || item.id === "dark") { selectTheme(item.id); return; }
        }
        if (item.kind === "theme") { selectTheme(item.id); return; }
        let operation, payload;
        if (item.kind === "app") { operation = "launch"; payload = {id:item.id}; }
        else if (item.kind === "calculator") { operation = "copy"; payload = {text:item.copyText}; }
        else if (item.kind === "clipboard") { operation = "copy-history"; payload = {id:item.id}; }
        else if (item.kind === "wallpaper") { operation = "wallpaper"; payload = {path:item.id}; }
        else if (["integration-open","steam-game","minecraft-instance"].includes(item.kind)) { operation="integration-launch";payload={source:item.source,id:item.id}; }
        else if (item.kind === "action") { operation = item.id; payload = {}; }
        else { operation = "terminal"; payload = {command:item.title}; }
        actionBusy = true; message = "";
        writer.exec(["python3", Quickshell.shellPath("scripts/launcher_backend.py"), operation, JSON.stringify(payload)]);
    }
    function selectTheme(id) {
        actionBusy = true; selectingTheme = true; message = "";
        ThemeStore.select(id);
    }
    Connections {
        target: ThemeStore
        function onThemesChanged() { if (root.opened && root.mode === "commands" && root.commandSection === "themes") root.rebuild(); }
        function onOperationFinished(operation, ok) {
            if (!root.selectingTheme || operation !== "select") return;
            root.selectingTheme = false; root.actionBusy = false;
            if (ok) root.close(); else root.message = ThemeStore.message;
        }
    }
    Timer {
        id: closeFallback
        interval: Theme.morphDuration + 100
        onTriggered: root.finishClose()
    }
    Timer {
        id: debounce; interval: 140
        onTriggered: {
            if (root.mode === "calculator" && root.query.slice(1).trim()) root.requestRead("calculate", {expression:root.query.slice(1).trim()});
            if (root.mode === "clipboard") root.requestRead("history", {});
            if (root.mode === "commands" && root.commandSection === "wallpapers") root.requestRead("wallpapers", {});
            if (root.mode === "commands" && ["steam","localsend","minecraft"].includes(root.commandSection)) root.requestRead("integration-list",{source:root.commandSection});
        }
    }
    Process {
        id: reader
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    if (root.opened && root.reading && root.reading.query === root.query) {
                        if (!response.ok) root.message = response.error;
                        else if (root.reading.operation === "history") {
                            root.clipboardRows = response.rows;
                            root.results = Search.clipboard(response.rows, root.query.slice(1));
                        } else if (root.reading.operation === "wallpapers") {
                            root.wallpaperRows = response.rows;
                            root.results = Search.filterRows(response.rows, root.commandFilter);
                            if (!response.rows.length) root.message = "Adicione imagens em ~/Pictures/Wallpapers.";
                        } else if (root.reading.operation === "integration-list") {
                            root.integrationSource=root.reading.payload.source;root.integrationRows=response.rows;
                            root.results=Search.filterRows(response.rows,root.commandFilter);
                        } else root.results = [{kind:"calculator",title:response.result,copyText:response.result,detail:"Enter para copiar o resultado",icon:"accessories-calculator"}];
                    }
                } catch (_) { if (root.opened) root.message = "Não foi possível consultar os resultados."; }
                root.readReceived = true; if (!reader.running) root.finishRead();
            }
        }
        onExited: root.finishRead()
    }
    Process {
        id: writer
        stdout: StdioCollector {
            onStreamFinished: {
                root.actionBusy = false;
                try { const response = JSON.parse(text); if (response.ok) root.close(); else root.message = response.error; }
                catch (_) { root.message = "A ação não respondeu."; }
            }
        }
    }
    IpcHandler {
        target: "launcher"
        function open(screenName: string): void { root.open(screenName); }
        function close(): void { root.close(); }
        function search(query: string): void { if (root.opened && query.length <= 2048) root.query = query; }
        function activate(): void { root.activate(); }
        function status(): string { return JSON.stringify({enabled:root.enabled,opened:root.opened,present:root.present,mode:root.mode,
            screenName:root.screenName,resultCount:root.results.length,selectedIndex:root.selectedIndex,
            busy:root.actionBusy || root.readBusy,message:root.message,
            calculatorResult:root.mode === "calculator" && root.results[0] ? root.results[0].title : ""}); }
    }
}
