// Integração opt-in: simula a API pública v2 e entrega eventos ao IPC real.
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";
import plugin from "../integrations/opencode-v2/index.js";
import { mapEvent } from "../integrations/opencode-v2/map-event.mjs";

const cli = fileURLToPath(new URL("../scripts/activity_cli.py", import.meta.url));
process.env.ILHA_ACTIVITY_SCRIPT = cli;
const sessionID = "adapter-test-" + process.pid;
const event = type => ({ type, data: { sessionID } });
const id = mapEvent(event("session.execution.started")).id;
const queue = [];
let wake = null;
const push = type => { queue.push(event(type)); if (wake) { wake(); wake = null; } };
const current = () => JSON.parse(execFileSync("python3", [cli, "list"], { encoding: "utf8" }))
    .activities.find(item => item.id === id);
const waitFor = async predicate => {
    for (let n = 0; n < 30; n++) {
        if (predicate(current())) return;
        await delay(100);
    }
    throw new Error("O adaptador não atualizou a atividade no prazo.");
};
const cleanup = plugin.setup({
    location: { directory: "/tmp/ilha-test" },
    event: {
        async *subscribe({ signal }) {
            signal.addEventListener("abort", () => { if (wake) wake(); }, { once: true });
            while (!signal.aborted) {
                if (queue.length) yield queue.shift();
                else await new Promise(resolve => { wake = resolve; });
            }
        },
    },
});
try {
    push("session.execution.started");
    await waitFor(item => item?.state === "running");
    push("permission.asked");
    await waitFor(item => item?.state === "waiting");
    push("session.execution.succeeded");
    await waitFor(item => item?.state === "success");
    cleanup();
    await waitFor(item => !item);
    assert.equal(current(), undefined);
    console.log("OK: adaptador OpenCode v2 → CLI → IPC, estados e limpeza.");
} finally {
    cleanup();
}
