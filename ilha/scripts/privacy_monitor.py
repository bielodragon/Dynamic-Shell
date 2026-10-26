#!/usr/bin/env python3
"""Observa metadados do PipeWire; não abre dispositivos nem lê áudio/vídeo."""
import json
import codecs
import os
import signal
import subprocess
import sys


def merge(old, delta):
    result = dict(old)
    for key, value in delta.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = merge(result.get(key, {}), value)
        else:
            result[key] = value
    return result


class Graph:
    def __init__(self):
        self.objects = {}

    def update(self, batch):
        for obj in batch:
            identifier = obj['id']
            # pw-dump anuncia remoções sem info, ou com info nulo.
            if 'info' not in obj or obj['info'] is None:
                self.objects.pop(identifier, None)
            else:
                self.objects[identifier] = merge(self.objects.get(identifier, {}), obj)

    def snapshot(self):
        active = {'microphone': [], 'camera': [], 'screen': [], 'video': []}
        nodes = {i: o['info'] for i, o in self.objects.items()
                 if o.get('type', '').endswith(':Node')}
        for identifier, info in nodes.items():
            if info.get('state') != 'running':
                continue
            props = info.get('props', {})
            kind = props.get('media.class', '')
            name = str(props.get('node.name', ''))
            role = str(props.get('media.role', '')).lower()
            category = None
            if kind == 'Audio/Source' and not name.endswith('.monitor'):
                # Exige conexão de captura ativa; disponibilidade do dispositivo não basta.
                for obj in self.objects.values():
                    link = obj.get('info', {})
                    lp = link.get('props', {})
                    target = nodes.get(lp.get('link.input.node'), {}).get('props', {})
                    if (obj.get('type', '').endswith(':Link')
                            and link.get('state') == 'active'
                            and lp.get('link.output.node') == identifier
                            and target.get('media.class') == 'Stream/Input/Audio'):
                        category = 'microphone'
                        break
            elif kind == 'Video/Source':
                if role == 'camera' or props.get('device.api') in ('v4l2', 'libcamera'):
                    category = 'camera'
                elif role == 'screen' or name in ('xdg-desktop-portal-hyprland', 'xdg-desktop-portal-wlr'):
                    category = 'screen'
                else:
                    # Não adivinhar câmera/tela quando o produtor não se identifica.
                    category = 'video'
            if category:
                active[category].append(str(props.get('node.description') or name or category)[:100])
        return {'ready': True, **{key: sorted(set(value)) for key, value in active.items()}}


def main():
    child = subprocess.Popen(['pw-dump', '-m', '-N'], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
    def stop(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    graph, buffer, previous = Graph(), '', None
    decoder = json.JSONDecoder()
    utf8 = codecs.getincrementaldecoder('utf-8')()
    try:
        while data := os.read(child.stdout.fileno(), 65536):
            buffer += utf8.decode(data)
            while buffer.strip():
                buffer = buffer.lstrip()
                try:
                    batch, end = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                buffer = buffer[end:]
                graph.update(batch)
                current = graph.snapshot()
                if current != previous:
                    print(json.dumps(current, ensure_ascii=False), flush=True)
                    previous = current
            if len(buffer) > 16 * 1024 * 1024:
                raise ValueError('Evento PipeWire excedeu o limite.')
    finally:
        child.terminate()
        child.wait(timeout=3)
        print(json.dumps({'ready': False}), flush=True)


if __name__ == '__main__':
    main()
