// Modelo puro, compartilhado pelo serviço QML e pelos testes de protocolo.
function textField(value, label, maxLength) {
    if (typeof value !== "string" || value.length > maxLength)
        throw new Error(label + " inválido.");
    return value.trim();
}

function apply(items, payload, now) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload))
        throw new Error("A atividade precisa ser um objeto JSON.");
    var id = textField(payload.id, "Identificador", 128);
    if (!/^[a-zA-Z0-9._:-]+$/.test(id)) throw new Error("Identificador inválido.");
    var previous = items.find(function(item) { return item.id === id; });
    if (!previous && items.length >= 16) throw new Error("Limite de 16 atividades atingido.");
    var value = Object.assign({}, previous || {
        id: id, title: "", app: "Programa", detail: "", state: "running", progress: null
    }, payload);
    value.title = textField(value.title, "Título", 120);
    if (!value.title) throw new Error("Informe um título.");
    value.app = textField(value.app, "Aplicativo", 60);
    value.detail = textField(value.detail, "Detalhes", 300);
    if (!["running", "waiting", "paused", "success", "error"].includes(value.state))
        throw new Error("Estado inválido.");
    if (value.progress !== null && (typeof value.progress !== "number"
            || !Number.isFinite(value.progress) || value.progress < 0 || value.progress > 100))
        throw new Error("Progresso precisa estar entre 0 e 100, ou null.");
    var ttl = payload.ttl === undefined
        ? (["success", "error"].includes(value.state) ? 8 : 3600) : payload.ttl;
    if (typeof ttl !== "number" || !Number.isFinite(ttl) || ttl < 1 || ttl > 86400)
        throw new Error("Duração precisa estar entre 1 e 86400 segundos.");
    // Apenas campos do protocolo entram no estado; nenhum comando é executado.
    var result = { id: id, title: value.title, app: value.app, detail: value.detail,
        state: value.state, progress: value.progress, updatedAt: now, expiresAt: now + ttl * 1000 };
    return [result].concat(items.filter(function(item) { return item.id !== id; }));
}

function prune(items, now) {
    return items.filter(function(item) { return item.expiresAt > now; });
}
