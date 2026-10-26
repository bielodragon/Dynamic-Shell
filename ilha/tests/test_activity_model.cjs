const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const model = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../components/ActivityModel.js"), "utf8"), model);

test("atualização mantém identidade e rejeita dados inválidos sem alterar a lista", () => {
    const initial = model.apply([], { id: "build:1", title: "Compilando", progress: 30 }, 1000);
    const next = model.apply(initial, { id: "build:1", progress: 75 }, 2000);
    assert.equal(next.length, 1);
    assert.equal(next[0].title, "Compilando");
    assert.equal(next[0].progress, 75);
    for (const payload of [
        { id: "build:1", progress: 101 }, { id: "build:1", progress: true },
        { id: "build:1", progress: NaN }, { id: "build:1", ttl: -1 },
        { id: "build:1", state: "invented" }, { id: "bad id", title: "x" },
        { id: "new" }, null,
    ]) assert.throws(() => model.apply(next, payload, 2500));
    assert.equal(next[0].progress, 75);
});

test("atividade concluída expira e progresso indeterminado pode substituir uma porcentagem", () => {
    let items = model.apply([], { id: "a", title: "Teste", progress: 40 }, 0);
    items = model.apply(items, { id: "a", progress: null }, 100);
    assert.equal(items[0].progress, null);
    items = model.apply(items, { id: "a", state: "success" }, 1000);
    assert.equal(model.prune(items, 8999).length, 1);
    assert.equal(model.prune(items, 9000).length, 0);
});

test("limite preserva atividades existentes e não incorpora comandos arbitrários", () => {
    let items = [];
    for (let i = 0; i < 16; i++) items = model.apply(items, { id: "a" + i, title: "x" }, 0);
    assert.throws(() => model.apply(items, { id: "a16", title: "x" }, 0));
    assert.equal(model.apply(items, { id: "a0", title: "Atualizado" }, 0).length, 16);
    assert.equal("command" in model.apply([], { id: "x", title: "x", command: "ignored" }, 0)[0], false);
});

test("OpenCode v2 usa eventos de execução e não os eventos idle/status da v1", async () => {
    const { mapEvent } = await import("../integrations/opencode-v2/map-event.mjs");
    const event = type => ({ type, data: { sessionID: "ses_example" } });
    const start = mapEvent(event("session.execution.started"));
    assert.equal(start.state, "running");
    const end = mapEvent(event("session.execution.succeeded"));
    assert.equal(end.id, start.id);
    assert.equal(end.state, "success");
    assert.equal(end.progress, null);
    assert.equal(mapEvent(event("permission.asked")).state, "waiting");
    assert.equal(mapEvent(event("session.execution.failed")).state, "error");
    assert.equal(mapEvent(event("session.deleted")).remove, start.id);
    assert.equal(mapEvent(event("session.idle")), null);
});
