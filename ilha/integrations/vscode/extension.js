'use strict';
const vscode=require('vscode');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {randomUUID}=require('node:crypto');
const {observe}=require('./activities');
let shutdown=()=>{};

function activate(context) {
    const channel=vscode.window.createOutputChannel('Ilha');context.subscriptions.push(channel);
    const config=()=>vscode.workspace.getConfiguration('ilhaActivities');
    let child=null,observer=null,disposed=false,retry=null;
    function bridgePath() {
        const explicit=config().get('bridgePath','');
        if (explicit) return fs.existsSync(explicit)?explicit:null;
        const roots=[process.env.XDG_CONFIG_HOME || path.join(os.homedir(),'.config'),
            ...(process.env.XDG_CONFIG_DIRS || '/etc/xdg').split(':')];
        return roots.map(root=>path.join(root,'quickshell/ilha/scripts/ide_activity_bridge.py')).find(file=>fs.existsSync(file));
    }
    function connect() {
        if (child || disposed || !config().get('enabled',true)) return child;
        const bridge=bridgePath();
        if (!bridge) {channel.appendLine('Ilha não encontrada. Instale o shell ou configure ilhaActivities.bridgePath.');return null;}
        const app=/codium/i.test(vscode.env.appName)?'vscodium':'vscode';
        const processChild=spawn('python3',[bridge,'--app',app],{stdio:['pipe','ignore','pipe'],shell:false});
        child=processChild;
        processChild.stdin.on('error',()=>{});
        // Diagnóstico genérico; nunca replicar um payload ou saída privada no canal.
        processChild.stderr.on('data',()=>channel.appendLine('A ponte da Ilha recusou um evento ou encontrou um erro.'));
        processChild.on('error',()=>channel.appendLine('Não foi possível iniciar a ponte Python da Ilha.'));
        processChild.on('close',()=>{
            if (child===processChild) child=null;
            if (!disposed && observer && observer.snapshot().length && config().get('enabled',true)) {
                retry=setTimeout(()=>{retry=null;for (const event of observer.snapshot()) send(event);},3000);
            }
        });
        return child;
    }
    function send(event) {
        const bridge=connect();if (!bridge || bridge.stdin.destroyed) return;
        bridge.stdin.write(JSON.stringify(event)+'\n');
    }
    observer=observe(vscode,send,()=>config().get('enabled',true),()=>config().get('terminal',true));
    context.subscriptions.push(observer);
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(event=>{
        if (event.affectsConfiguration('ilhaActivities') && !config().get('enabled',true)) observer.clear();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('ilhaActivities.preview',()=>{
        if (!config().get('enabled',true)) return;
        const id=randomUUID();send({op:'start',id,kind:'task'});
        const timer=setTimeout(()=>{if (!disposed) send({op:'end',id,exitCode:0});},5000);
        context.subscriptions.push({dispose:()=>clearTimeout(timer)});
    }));
    shutdown=()=>{
        disposed=true;if (retry) clearTimeout(retry);
        observer.dispose();
        if (child) {const closing=child;closing.stdin.end();setTimeout(()=>{if (closing.exitCode===null) closing.kill();},1000).unref();child=null;}
    };
    context.subscriptions.push({dispose:shutdown});
}
function deactivate() {shutdown();}
module.exports={activate,deactivate};
