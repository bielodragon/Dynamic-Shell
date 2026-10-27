'use strict';
const {randomUUID}=require('node:crypto');

// Objetos de execução são chaves opacas: não lemos task.definition, commandLine ou logs.
function observe(vscode,send,enabled=()=>true,terminalEnabled=()=>true) {
    const entries=new Map(),subscriptions=[];
    function start(key,kind,terminal) {
        if (!enabled() || entries.has(key) || entries.size>=8) return;
        const id=randomUUID();entries.set(key,{id,kind,terminal});send({op:'start',id,kind});
    }
    function end(key,exitCode) {
        const entry=entries.get(key);if (!entry) return;
        entries.delete(key);send({op:'end',id:entry.id,exitCode:Number.isInteger(exitCode)?exitCode:null});
    }
    function listen(event,callback) { if (typeof event==='function') subscriptions.push(event(callback)); }
    listen(vscode.tasks.onDidStartTask,event=>start(event.execution,'task'));
    listen(vscode.tasks.onDidEndTaskProcess,event=>end(event.execution,event.exitCode));
    // Alguns CustomExecution não têm código de saída. Nunca anunciar sucesso nesses casos.
    listen(vscode.tasks.onDidEndTask,event=>end(event.execution,null));
    listen(vscode.debug.onDidStartDebugSession,session=>start(session,'debug'));
    listen(vscode.debug.onDidTerminateDebugSession,session=>end(session,null));
    listen(vscode.window.onDidStartTerminalShellExecution,event=>{
        if (terminalEnabled()) start(event.execution,'terminal',event.terminal);
    });
    listen(vscode.window.onDidEndTerminalShellExecution,event=>end(event.execution,event.exitCode));
    listen(vscode.window.onDidCloseTerminal,terminal=>{
        for (const [key,value] of entries) if (value.terminal===terminal) end(key,null);
    });
    for (const execution of vscode.tasks.taskExecutions || []) start(execution,'task');
    if (vscode.debug.activeDebugSession) start(vscode.debug.activeDebugSession,'debug');
    return {
        snapshot:()=>Array.from(entries.values(),({id,kind})=>({op:'start',id,kind})),
        clear() {for (const key of entries.keys()) end(key,null);},
        dispose() {this.clear();for (const subscription of subscriptions) subscription.dispose();}
    };
}
module.exports={observe};
