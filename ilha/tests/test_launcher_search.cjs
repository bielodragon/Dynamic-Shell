const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const code = fs.readFileSync(__dirname + '/../components/LauncherSearch.js', 'utf8').replace(/^\.pragma library\s*/, '');
const model = vm.createContext({}); vm.runInContext(code, model);
test('busca ignora acentos e prioriza nome exato e prefixo', () => {
    assert.equal(model.normalized('Configurações'), 'configuracoes');
    assert.ok(model.score('Firefox', '', 'firefox') > model.score('Firefox Nightly', '', 'firefox'));
    assert.ok(model.score('Firefox Nightly', '', 'fire') > model.score('Meu Firefox', '', 'fire'));
    assert.equal(model.score('Terminal', '', 'xyz'), 0);
});
test('busca fuzzy e palavras-chave encontram apps sem executar seus métodos', () => {
    let executed = false;
    const rows = model.apps([{ id:'f', name:'Firefox', keywords:['browser'], execute() {executed=true;} }], 'frfx');
    assert.equal(rows.length, 1); assert.equal(rows[0].id, 'f');
    assert.equal(model.apps([{id:'f',name:'Firefox',keywords:['browser']}], 'browser').length, 1);
    assert.equal(executed, false);
});
test('prefixo de ações mostra catálogo e encontra aliases sem executar comandos', () => {
    assert.equal(model.actions('').length, 6);
    for (const [query, id] of [['lock','lock'],['light','light'],['dark','dark'],['schema','themes'],['random','random-wallpaper']]) {
        assert.equal(model.actions(query)[0].id, id);
    }
    assert.equal(model.actions('printf "%s" "$(literal)"').length, 0);
});
