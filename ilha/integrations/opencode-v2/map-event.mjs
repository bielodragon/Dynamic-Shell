import { createHash } from "node:crypto";

// Eventos v2 usam data.sessionID, em vez de properties.sessionID da v1.
export function mapEvent(event) {
    const session = event?.data?.sessionID;
    if (typeof session !== "string" || !session) return null;
    const id = "opencode:" + createHash("sha256").update(session).digest("hex").slice(0, 24);
    if (event.type === "session.deleted") return { remove: id };
    const states = {
        "session.execution.started": ["running", "OpenCode trabalhando"],
        "session.step.started": ["running", "OpenCode trabalhando"],
        "session.tool.called": ["running", "OpenCode executando ferramenta"],
        "session.execution.succeeded": ["success", "OpenCode respondeu"],
        "session.execution.failed": ["error", "OpenCode: erro na resposta"],
        "session.execution.interrupted": ["paused", "OpenCode interrompido"],
        "session.retry.scheduled": ["waiting", "OpenCode: nova tentativa"],
        "permission.asked": ["waiting", "OpenCode aguarda você"],
        "permission.replied": event.data.reply === "reject"
            ? ["paused", "OpenCode: permissão recusada"] : ["running", "OpenCode trabalhando"],
    };
    const state = states[event.type];
    if (!state) return null;
    return { id, app: "OpenCode", title: state[1], state: state[0],
        detail: "", progress: null,
        ttl: ["success", "error", "paused"].includes(state[0]) ? 12 : 3600 };
}
