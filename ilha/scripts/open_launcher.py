#!/usr/bin/env python3
"""Abre a pesquisa a partir da ilha do monitor em foco."""
import json
import subprocess
import sys


def main():
    try:
        monitors = json.loads(subprocess.check_output(
            ["hyprctl", "-j", "monitors"], text=True, timeout=3))
        monitor = next((item for item in monitors if item.get("focused")), None)
        if not monitor:
            raise ValueError("Nenhum monitor em foco disponível.")
        subprocess.run([
            "/usr/bin/quickshell", "-c", "ilha", "ipc", "call",
            "ilha." + monitor["name"], "openLauncher",
        ], check=True, timeout=5)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Não foi possível abrir a pesquisa da Ilha: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
