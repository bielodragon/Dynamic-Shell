"""Cliente IPC das atividades. Textos são argumentos, nunca código de shell."""
import argparse
import json
import os
import subprocess
import sys


def request(method, value=None):
    command = [os.environ.get("ILHA_QUICKSHELL", "/usr/bin/quickshell"),
               "-c", os.environ.get("ILHA_CONFIG", "ilha"), "ipc", "call", "activities", method]
    if value is not None:
        command.append(json.dumps(value, ensure_ascii=False, allow_nan=False) if method == "update" else value)
    result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    if result.returncode:
        raise RuntimeError("A Ilha não está disponível. Inicie quickshell -c ilha.")
    response = json.loads(result.stdout)
    if not response.get("ok"):
        raise ValueError(response.get("error", "Atividade recusada."))
    return response


def main():
    parser = argparse.ArgumentParser(description="Envia atividades de qualquer programa à Ilha.")
    sub = parser.add_subparsers(dest="operation", required=True)
    update = sub.add_parser("update", help="Cria ou atualiza uma atividade pelo identificador.")
    update.add_argument("id")
    update.add_argument("--title")
    update.add_argument("--app")
    update.add_argument("--detail")
    update.add_argument("--state", choices=["running", "waiting", "paused", "success", "error"])
    progress = update.add_mutually_exclusive_group()
    progress.add_argument("--progress", type=float, help="Progresso real, de 0 a 100.")
    progress.add_argument("--indeterminate", action="store_true")
    update.add_argument("--ttl", type=float, help="Segundos até expirar (padrão: 1 h; estado final: 8 s).")
    done = sub.add_parser("done", help="Mostra conclusão por oito segundos.")
    done.add_argument("id")
    done.add_argument("--title")
    remove = sub.add_parser("remove")
    remove.add_argument("id")
    sub.add_parser("list")
    sub.add_parser("send", help="Lê um objeto JSON de stdin.")
    args = parser.parse_args()
    try:
        if args.operation == "list":
            response = request("list")
        elif args.operation == "remove":
            response = request("remove", args.id)
        else:
            if args.operation == "send":
                raw = sys.stdin.read(4097)
                if len(raw) > 4096:
                    raise ValueError("Atividade maior que 4 KiB.")
                payload = json.loads(raw)
            else:
                payload = {key: value for key, value in vars(args).items()
                           if key not in ("operation", "indeterminate") and value is not None}
                if args.operation == "done":
                    payload.update(state="success", progress=100)
                elif args.indeterminate:
                    payload["progress"] = None
            response = request("update", payload)
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
