const test=require('node:test');
const assert=require('node:assert/strict');
const {observe}=require('../integrations/vscode/activities');
function event() {
    const listeners=new Set();
    const subscribe=callback=>{listeners.add(callback);return {dispose:()=>listeners.delete(callback)};};
    subscribe.fire=value=>{for(const callback of listeners) callback(value);};return subscribe;
}
function fixture() {
    const api={tasks:{taskExecutions:[],onDidStartTask:event(),onDidEndTaskProcess:event(),onDidEndTask:event()},
        debug:{onDidStartDebugSession:event(),onDidTerminateDebugSession:event()},
        window:{onDidStartTerminalShellExecution:event(),onDidEndTerminalShellExecution:event(),onDidCloseTerminal:event()}};
    const sent=[];const observer=observe(api,payload=>sent.push(payload));return {api,sent,observer};
}
const secret=new Proxy({}, {get(){throw new Error('Não ler comando, nome, definição ou log.');}});
test('tarefa: execução opaca, código de saída e evento final duplicado',()=>{
    const {api,sent,observer}=fixture();
    api.tasks.onDidStartTask.fire({execution:secret});
    api.tasks.onDidEndTaskProcess.fire({execution:secret,exitCode:7});
    api.tasks.onDidEndTask.fire({execution:secret});
    assert.equal(sent.length,2);assert.equal(sent[1].exitCode,7);assert.equal(sent[0].id,sent[1].id);
    assert.deepEqual(observer.snapshot(),[]);observer.dispose();
});
test('debug não é declarado bem-sucedido e terminal não lê commandLine/read()',()=>{
    const {api,sent,observer}=fixture();
    api.debug.onDidStartDebugSession.fire(secret);api.debug.onDidTerminateDebugSession.fire(secret);
    api.window.onDidStartTerminalShellExecution.fire({execution:secret,terminal:secret});
    api.window.onDidEndTerminalShellExecution.fire({execution:secret,exitCode:0});
    assert.equal(sent[0].kind,'debug');assert.equal(sent[1].exitCode,null);
    assert.equal(sent[2].kind,'terminal');assert.equal(sent[3].exitCode,0);observer.dispose();
});
test('fechar terminal e desativar extensão encerram somente IDs próprios',()=>{
    const {api,sent,observer}=fixture();
    const execution={};api.window.onDidStartTerminalShellExecution.fire({execution,terminal:secret});
    api.window.onDidCloseTerminal.fire(secret);assert.equal(sent[1].exitCode,null);
    api.tasks.onDidStartTask.fire({execution:secret});observer.dispose();
    assert.equal(sent.length,4);api.tasks.onDidStartTask.fire({execution:{}});assert.equal(sent.length,4);
});
test('limite de atividades e preferências desligadas',()=>{
    const {api,observer}=fixture();observer.dispose();const sent=[];
    const disabled=observe(api,event=>sent.push(event),()=>false,()=>false);
    api.tasks.onDidStartTask.fire({execution:secret});assert.equal(sent.length,0);disabled.dispose();
    const enabled=observe(api,event=>sent.push(event));
    for(let i=0;i<12;i++) api.tasks.onDidStartTask.fire({execution:{}});
    assert.equal(enabled.snapshot().length,8);enabled.dispose();
});
