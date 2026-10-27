pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Singleton {
    id: root
    property var themes: []
    property var config: ({ theme: "dark", overrides: {} })
    property string message: ""
    property bool messageIsError: false
    property bool ready: false
    property bool busy: false
    property bool responseReceived: false
    property var jobs: []
    property string currentOperation: ""
    property var currentPayload: ({})
    signal operationFinished(string operation, bool ok)

    readonly property var selectedTheme: themes.find(item => item.id === config.theme) || null

    function next() {
        if (busy || jobs.length === 0) return;
        const job = jobs.shift();
        currentOperation = job.operation;
        currentPayload = job.payload;
        busy = true;
        responseReceived = false;
        worker.exec(["python3", Quickshell.shellPath("scripts/theme_store.py"), job.operation, JSON.stringify(job.payload)]);
    }

    function run(operation, payload) {
        jobs.push({ operation: operation, payload: payload || {} });
        next();
    }

    function receive(response) {
        if (!response.ok) {
            message = response.error || "Falha ao salvar tema.";
            messageIsError = true;
            operationFinished(currentOperation, false);
            return;
        }
        themes = response.themes;
        config = response.config;
        ready = true;
        const descriptions = { select: "Tema aplicado.", save: "Tema salvo.", duplicate: "Tema duplicado.", delete: "Tema apagado.", import: "Tema importado.", export: "JSON exportado.", overrides: "Ajustes salvos." };
        message = descriptions[currentOperation] || "";
        messageIsError = false;
        if (selectedTheme) Theme.apply(selectedTheme, config.overrides);
        // Não reaplicar o wallpaper do tema ao selecionar outro fundo ou pausar sua animação.
        if (["snapshot","select","save","duplicate","delete","import","overrides"].includes(currentOperation)
            || (currentOperation === "preferences" && (currentPayload.values.sync || currentPayload.values.wallpapers))) ThemeSync.schedule();
        operationFinished(currentOperation, true);
    }

    function finish() {
        if (!responseReceived) return;
        busy = false;
        next();
    }

    function preview(theme) { Theme.apply(theme, config.overrides); }
    function restore() { if (selectedTheme) Theme.apply(selectedTheme, config.overrides); }
    function select(id) { run("select", { id: id }); }
    function save(theme, id) { run("save", { theme: theme, id: id || "" }); }
    function duplicate(id) { run("duplicate", { id: id }); }
    function remove(id) { run("delete", { id: id }); }
    function importFile(path) { run("import", { path: path }); }
    function exportFile(id, path) { run("export", { id: id, path: path }); }
    function setOverrides(values) { run("overrides", { values: values }); }
    function setWorkspaceStyle(style) { run("workspace_style", { style: style }); }
    function setDoNotDisturb(enabled) { run("do_not_disturb", { enabled: enabled }); }
    function setPreferences(values) { run("preferences", { values: values }); }

    Component.onCompleted: run("snapshot", {})

    Process {
        id: worker
        stdout: StdioCollector {
            id: output
            onStreamFinished: {
                try {
                    root.receive(JSON.parse(text));
                } catch (error) {
                    root.message = "Não foi possível ler o retorno do armazenamento de temas.";
                    root.messageIsError = true;
                    root.operationFinished(root.currentOperation, false);
                }
                root.responseReceived = true;
                if (!worker.running) root.finish();
            }
        }
        stderr: StdioCollector { id: errors }
        onExited: function(exitCode, exitStatus) {
            root.finish();
        }
    }
}
