#!/usr/bin/env python3
"""Ações do launcher. Digitar pesquisa nunca executa aplicativos ou comandos."""
import ast
import json
import math
import operator
import os
import re
import shutil
import subprocess
import sys


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 256:
        raise ValueError('Digite uma expressão de até 256 caracteres.')
    tree = ast.parse(expression, mode='eval')
    if len(list(ast.walk(tree))) > 64: raise ValueError('Expressão longa demais.')
    binary = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
              ast.Div:operator.truediv, ast.FloorDiv:operator.floordiv, ast.Mod:operator.mod, ast.Pow:operator.pow}
    functions = {'sqrt':math.sqrt, 'sin':math.sin, 'cos':math.cos, 'tan':math.tan,
                 'log':math.log, 'log10':math.log10, 'abs':abs, 'round':round}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): value = node.value
        elif isinstance(node, ast.Name) and node.id in ('pi', 'e'): value = getattr(math, node.id)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in binary:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100: raise ValueError('Expoente máximo: 100.')
            value = binary[type(node.op)](left, right)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions and not node.keywords and 1 <= len(node.args) <= 2:
            value = functions[node.func.id](*(visit(arg) for arg in node.args))
        else: raise ValueError('Use números, operações, pi, e ou funções matemáticas simples.')
        if type(value) not in (int, float) or abs(value) > 1e100 or not math.isfinite(value):
            raise ValueError('Resultado fora do intervalo permitido.')
        return value
    value = visit(tree.body)
    return str(value) if isinstance(value, int) else format(value, '.12g')


def clip_command(operation):
    command = ['cliphist']
    # Permite testes em banco privado; não lê nem substitui o banco pessoal nesses testes.
    if os.environ.get('ILHA_CLIPHIST_DB'): command += ['-db-path', os.environ['ILHA_CLIPHIST_DB']]
    return command + [operation]


def history():
    process = subprocess.run(clip_command('list'), capture_output=True, timeout=4)
    if process.returncode:
        raise RuntimeError('Histórico indisponível ou vazio. O cliphist precisa de um observador wl-paste ativo.')
    rows = []
    for line in process.stdout.decode('utf-8', errors='replace').splitlines()[:60]:
        identifier, separator, text = line.partition('\t')
        if separator and identifier.isdigit():
            rows.append({'kind':'clipboard', 'id':identifier, 'title':text[:180], 'detail':'Copiar para a área de transferência', 'icon':'edit-paste'})
    return rows


def copy(data):
    if len(data) > 8 * 1024 * 1024: raise ValueError('Item maior que 8 MiB.')
    result = subprocess.run(['wl-copy'], input=data, capture_output=True, timeout=4)
    if result.returncode: raise RuntimeError('Não foi possível copiar para a área de transferência.')


def launch_app(identifier):
    from gi.repository import Gio
    if not isinstance(identifier, str) or not identifier or len(identifier) > 256 or any(c in identifier for c in '/\\\x00\n'):
        raise ValueError('Aplicativo inválido.')
    desktop_id = identifier if identifier.endswith('.desktop') else identifier + '.desktop'
    app = Gio.DesktopAppInfo.new(desktop_id)
    if not app or not app.should_show(): raise ValueError('Aplicativo não encontrado.')
    # Gio interpreta Desktop Entry, diretório e Terminal=true; não reconstruir Exec como shell.
    if not app.launch([], None): raise RuntimeError('O aplicativo não iniciou.')


def terminal(command):
    if not isinstance(command, str) or not command.strip() or len(command) > 2048 or '\x00' in command:
        raise ValueError('Comando vazio ou longo demais.')
    executable = shutil.which('xdg-terminal-exec')
    if executable: args = [executable, 'sh', '-lc', command]
    else:
        executable = shutil.which('foot') or shutil.which('kitty')
        if not executable: raise ValueError('Instale/configure um terminal para executar comandos.')
        args = [executable, 'sh', '-lc', command]
    # Aqui o shell é explícito: somente após Enter no modo "Executar no terminal".
    subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def perform(operation, payload):
    if operation == 'integration-list':
        from app_integrations import catalog
        return {'rows':catalog(payload.get('source'))}
    if operation == 'integration-launch':
        from app_integrations import launch
        launch(payload.get('source'),payload.get('id','client'));return {}
    if operation in ('wallpapers', 'wallpaper', 'random-wallpaper', 'lock'):
        import launcher_actions as actions
        if operation == 'wallpapers': return {'rows': actions.wallpapers()}
        if operation == 'wallpaper': actions.apply_wallpaper(payload.get('path', ''))
        elif operation == 'random-wallpaper': actions.random_wallpaper()
        else: actions.lock()
        return {}
    if operation == 'calculate': return {'result':calculate(payload.get('expression'))}
    if operation == 'history': return {'rows':history()}
    if operation == 'copy': copy(str(payload.get('text', '')).encode())
    elif operation == 'copy-history':
        identifier = str(payload.get('id', ''))
        if not re.fullmatch(r'\d{1,20}', identifier): raise ValueError('Identificador inválido.')
        result = subprocess.run(clip_command('decode'), input=(identifier + '\t\n').encode(), capture_output=True, timeout=4)
        if result.returncode: raise ValueError('Item removido ou indisponível no histórico.')
        copy(result.stdout)
    elif operation == 'launch': launch_app(payload.get('id'))
    elif operation == 'terminal': terminal(payload.get('command'))
    else: raise ValueError('Operação desconhecida.')
    return {}


if __name__ == '__main__':
    try:
        value = perform(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
        response = {'ok':True, **value}
    except Exception as error: response = {'ok':False, 'error':str(error)[:240]}
    print(json.dumps(response, ensure_ascii=False))
