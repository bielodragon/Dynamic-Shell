"""Execução e relay sem shell, com preservação do controle do terminal."""
import errno
import fcntl
import os
import pty
import select
import signal
import subprocess
import sys
import termios
import time
import tty


def relay(command,callback,heartbeat,interactive=False):
    saved=None;master=None;child=None;handlers={}
    stdin=sys.stdin.fileno();stdout=sys.stdout.fileno()
    try:
        if interactive:
            if not os.isatty(stdin):raise ValueError('Execute o LocalSend integrado em um terminal interativo.')
            master,slave=pty.openpty()
            def resize(*_):
                try:fcntl.ioctl(master,termios.TIOCSWINSZ,fcntl.ioctl(stdin,termios.TIOCGWINSZ,b'\0'*8))
                except OSError:pass
            resize()
            child=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
            os.close(slave);saved=termios.tcgetattr(stdin);tty.setraw(stdin)
            handlers[signal.SIGWINCH]=signal.signal(signal.SIGWINCH,resize)
            output=master
        else:
            child=subprocess.Popen(command,stdout=subprocess.PIPE)
            output=child.stdout.fileno()
        def forward(signum,frame):
            if child.poll() is None:child.send_signal(signum)
        for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):handlers[sig]=signal.signal(sig,forward)
        next_heartbeat=0;inputs=[output]+([stdin] if interactive else [])
        while True:
            ready,_,_=select.select(inputs,[],[],.3)
            if interactive and stdin in ready:
                data=os.read(stdin,8192)
                if data:os.write(master,data)
                else:inputs.remove(stdin)
            if output in ready:
                try:data=os.read(output,32768)
                except OSError as error:
                    if error.errno!=errno.EIO:raise
                    data=b''
                if not data:break
                os.write(stdout,data);callback(data)
            now=time.monotonic()
            if now>=next_heartbeat:heartbeat();next_heartbeat=now+1
            if child.poll() is not None and not ready:break
        result=child.wait()
        return result
    finally:
        if saved is not None:termios.tcsetattr(stdin,termios.TCSADRAIN,saved)
        for sig,handler in handlers.items():signal.signal(sig,handler)
        if master is not None:os.close(master)
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
