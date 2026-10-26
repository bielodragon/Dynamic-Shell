#!/usr/bin/env python3
"""Servidor OBS simulado em loopback + ObsState QML real; não controla o OBS pessoal."""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from obs_config import authentication

STATE = {'outputActive': False, 'outputPaused': False, 'outputDuration': 0}
REQUESTS = []
DROP = threading.Event()


def exact(stream, size):
    data = b''
    while len(data) < size:
        chunk = stream.recv(size - len(data))
        if not chunk:
            raise EOFError()
        data += chunk
    return data


def receive(stream):
    first, second = exact(stream, 2)
    if first & 15 == 8:
        raise EOFError()
    size = second & 127
    if size == 126:
        size = struct.unpack('!H', exact(stream, 2))[0]
    elif size == 127:
        size = struct.unpack('!Q', exact(stream, 8))[0]
    assert size < 65536
    assert second & 128, 'Cliente WebSocket deve mascarar frames.'
    mask = exact(stream, 4)
    payload = exact(stream, size)
    return json.loads(bytes(value ^ mask[i % 4] for i, value in enumerate(payload)))


def send(stream, op, data):
    payload = json.dumps({'op': op, 'd': data}).encode()
    header = bytes([129, len(payload)]) if len(payload) < 126 else b'\x81\x7e' + struct.pack('!H', len(payload))
    stream.sendall(header + payload)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            stream = self.request
            stream.settimeout(6)
            header = b''
            while not header.endswith(b'\r\n\r\n'):
                header += exact(stream, 1)
            fields = dict(line.split(': ', 1) for line in header.decode().split('\r\n')[1:] if ': ' in line)
            key = fields['Sec-WebSocket-Key']
            accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
            stream.sendall(('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + accept + '\r\n\r\n').encode())
            send(stream, 0, {'rpcVersion': 1, 'authentication': {'salt': 'test-salt', 'challenge': 'test-challenge'}})
            packet = receive(stream)
            assert packet['op'] == 1
            assert packet['d']['authentication'] == authentication('test-only-password', 'test-salt', 'test-challenge')
            assert packet['d']['eventSubscriptions'] == 66
            send(stream, 2, {'negotiatedRpcVersion': 1})
            while not DROP.is_set():
                packet = receive(stream)
                data = packet['d']
                assert packet['op'] == 6 and data['requestType'] == 'GetRecordStatus'
                REQUESTS.append(data['requestType'])
                send(stream, 7, {'requestType': data['requestType'], 'requestId': data['requestId'],
                     'requestStatus': {'result': True, 'code': 100}, 'responseData': dict(STATE)})
        except (EOFError, OSError):
            pass


def main():
    server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix='ilha-obs-test-') as directory:
        folder = Path(directory)
        for name in ('services', 'scripts', 'components'):
            (folder / name).symlink_to(ROOT / name, target_is_directory=True)
        (folder / 'shell.qml').write_text('''import Quickshell
import Quickshell.Io
import qs.services
ShellRoot {
    IpcHandler {
        target: "obs-test"
        function status(): string { return JSON.stringify(ObsState.snapshot()); }
    }
}''')
        config = folder / 'obs.json'
        config.write_text(json.dumps({'server_enabled': True, 'server_port': server.server_address[1],
                                     'server_password': 'test-only-password'}))
        env = dict(os.environ, ILHA_OBS_CONFIG=str(config))
        with (folder / 'qml.log').open('w+') as log:
            process = subprocess.Popen(['/usr/bin/quickshell', '-p', str(folder), '--no-color'],
                                       stdout=log, stderr=log, env=env)
            def wait_for(predicate):
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    result = subprocess.run(['/usr/bin/quickshell', 'ipc', '--pid', str(process.pid),
                        'call', 'obs-test', 'status'], capture_output=True, text=True, timeout=2)
                    try:
                        state = json.loads(result.stdout)
                        if predicate(state):
                            return state
                    except ValueError:
                        pass
                    time.sleep(.15)
                log.seek(0)
                raise AssertionError('Estado OBS esperado não chegou.\n' + log.read())
            try:
                wait_for(lambda s: s['available'] and not s['recording'])
                STATE.update(outputActive=True, outputDuration=62000)
                wait_for(lambda s: s['recording'] and s['durationMs'] == 62000)
                STATE.update(outputPaused=True)
                wait_for(lambda s: s['paused'] and s['durationMs'] == 62000)
                STATE.update(outputPaused=False, outputDuration=64000)
                wait_for(lambda s: not s['paused'] and s['durationMs'] == 64000)
                STATE.update(outputActive=False, outputDuration=0)
                wait_for(lambda s: not s['recording'] and s['durationMs'] == 0)
                DROP.set()
                wait_for(lambda s: not s['available'] and not s['recording'])
                assert len(REQUESTS) >= 5
                log.seek(0)
                assert 'ERROR' not in log.read()
                print('OK: autenticação, início, pausa, retomada, parada e desconexão OBS → QML real.')
            finally:
                process.terminate()
                process.wait(timeout=5)
                server.shutdown()
                server.server_close()


if __name__ == '__main__':
    main()
