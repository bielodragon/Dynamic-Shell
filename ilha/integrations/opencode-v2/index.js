import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { mapEvent } from "./map-event.mjs";

function deliver(payload) {
    const script = process.env.ILHA_ACTIVITY_SCRIPT
        || join(homedir(), ".config/quickshell/ilha/scripts/activity_cli.py");
    const args = payload.remove ? [script, "remove", payload.remove] : [script, "send"];
    return new Promise((resolve) => {
        const child = execFile("python3", args, { timeout: 3000, maxBuffer: 16384 }, () => resolve());
        child.stdin.on("error", () => {});
        child.stdin.end(payload.remove ? "" : JSON.stringify(payload));
    });
}

export default {
    id: "ilha.activities",
    setup(ctx) {
        const controller = new AbortController();
        const owned = new Set();
        void (async () => {
            while (!controller.signal.aborted) {
                try {
                    for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
                        const payload = mapEvent(event);
                        if (!payload) continue;
                        // Cada instância acompanha os eventos da sua localização.
                        if (event.location?.directory && ctx.location?.directory
                            && event.location.directory !== ctx.location.directory) continue;
                        if (payload.remove) owned.delete(payload.remove);
                        else owned.add(payload.id);
                        await deliver(payload);
                    }
                } catch {
                    if (controller.signal.aborted) break;
                }
                if (!controller.signal.aborted) await new Promise(resolve => setTimeout(resolve, 1500));
            }
        })();
        return () => {
            controller.abort();
            for (const id of owned) void deliver({ remove: id });
        };
    },
};
