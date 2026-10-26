"""Configuração reversível do desktop, sem remover shells existentes."""
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

BEGIN, END = '# >>> ilha >>>', '# <<< ilha <<<'


def config_root():
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))


def backup(path):
    target = Path(str(path) + '.bak.ilha-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    shutil.copy2(path, target)
    return target


def conflicts():
    found = []
    try:
        layers = json.loads(subprocess.check_output(['hyprctl','-j','layers'],text=True,timeout=3))
        names = {row.get('namespace','') for monitor in layers.values() for rows in monitor.get('levels',{}).values() for row in rows}
        for label, prefix in [('Caelestia','caelestia'),('Omarchy','omarchy'),('Waybar','waybar')]:
            if any(name.startswith(prefix) for name in names): found.append(label)
    except (OSError, ValueError, subprocess.SubprocessError): pass
    for name in ('mako','dunst'):
        try:
            if subprocess.run(['pgrep','-u',str(os.getuid()),'-x',name],capture_output=True,timeout=2).returncode == 0: found.append(name)
        except (OSError, subprocess.SubprocessError): pass
    return found


def hyprland_block(lua=True):
    cli = shlex.join(['python3',str(Path(__file__).with_name('desktop_cli.py').resolve())])
    if lua:
        # JSON fornece strings válidas de Lua para caminhos usuais; escapar sem shell.
        command = lambda value: json.dumps(cli + ' ' + value, ensure_ascii=False)
        return '\n'.join([
            '-- >>> ilha >>>',
            '-- Atalhos e inicialização da Ilha; arquivos de outros shells preservados.',
            'hl.layer_rule({ name = "ilha-glass", match = { namespace = "ilha-(island|themes|notifications|control-center|launcher)" }, blur = true, ignore_alpha = 0.1 })',
            'hl.layer_rule({ name = "ilha-launcher-morph", match = { namespace = "ilha-launcher" }, no_anim = true })',
            'hl.unbind("SUPER + SPACE")',
            'hl.bind("SUPER + SPACE", hl.dsp.exec_cmd(' + command('launcher') + '))',
            'hl.bind("SUPER + CTRL + I", hl.dsp.exec_cmd(' + command('island-toggle') + '))',
            'hl.bind("SUPER + CTRL + SHIFT + I", hl.dsp.exec_cmd(' + command('toggle') + '))',
            'hl.on("hyprland.start", function() hl.exec_cmd(' + command('start') + ') end)',
            '-- <<< ilha <<<', ''])
    return '\n'.join([BEGIN,
        'unbind = SUPER, SPACE',
        'bind = SUPER, SPACE, exec, ' + cli + ' launcher',
        'bind = SUPER CTRL, I, exec, ' + cli + ' island-toggle',
        'bind = SUPER CTRL SHIFT, I, exec, ' + cli + ' toggle',
        'exec-once = ' + cli + ' start', END, ''])


def prepare_hyprland(apply=False):
    root = config_root() / 'hypr'
    path = root / 'hyprland.lua'
    if not path.exists(): path = root / 'hyprland.conf'
    if not path.exists(): raise ValueError('Configuração Hyprland não encontrada; crie-a antes de usar ilha setup.')
    lua = path.suffix == '.lua'
    text = path.read_text()
    begin, end = ('-- >>> ilha >>>','-- <<< ilha <<<') if lua else (BEGIN,END)
    if begin in text:
        before, rest = text.split(begin,1)
        if end not in rest: raise ValueError('Bloco Ilha incompleto: confira o arquivo antes de atualizar.')
        text = before + rest.split(end,1)[1]
    content = text.rstrip() + '\n\n' + hyprland_block(lua)
    if not apply: return {'path':str(path),'block':hyprland_block(lua)}
    if not begin in path.read_text():
        binds = json.loads(subprocess.check_output(['hyprctl','-j','binds'],text=True,timeout=3))
        if any(str(bind.get('key','')).lower() == 'i' and bind.get('modmask') in (68,69) for bind in binds):
            raise ValueError('Ctrl+Super+I ou Ctrl+Shift+Super+I já está ocupado. Escolha outros atalhos antes de aplicar.')
    saved = backup(path)
    path.write_text(content)
    try:
        subprocess.run(['hyprctl','reload'],capture_output=True,text=True,check=True,timeout=5)
        errors = subprocess.check_output(['hyprctl','configerrors'],text=True,timeout=5).strip()
        if errors: raise RuntimeError(errors)
    except (OSError, RuntimeError, subprocess.SubprocessError):
        shutil.copy2(saved,path)
        subprocess.run(['hyprctl','reload'],capture_output=True,timeout=5)
        raise
    return {'path':str(path),'backup':str(saved)}


def bars(hide=False, restore=False):
    path = config_root() / 'caelestia/shell.json'
    state = config_root() / 'ilha/caelestia-bars.json'
    if not path.exists(): raise ValueError('Não encontrei configuração pessoal do Caelestia. Nenhum shell alterado.')
    data = json.loads(path.read_text())
    changes = {'bar':{'excludedScreens':['^.*$']},'sidebar':{'enabled':False}}
    if not hide and not restore: return {'path':str(path),'changes':changes}
    if restore:
        if not state.exists(): raise ValueError('Nenhuma alteração de barras da Ilha para restaurar.')
        previous = json.loads(state.read_text())
        for section, values in previous.items():
            for key, original in values.items():
                if data.get(section,{}).get(key) != changes[section][key]:
                    raise ValueError('A configuração foi alterada depois; restaure manualmente pelo backup para preservar seus ajustes.')
                if original['present']: data[section][key] = original['value']
                else: data[section].pop(key,None)
    else:
        if state.exists(): return {'message':'As barras já foram configuradas pela Ilha.'}
        previous = {section:{key:{'present':key in data.get(section,{}),'value':data.get(section,{}).get(key)} for key in values} for section,values in changes.items()}
        state.parent.mkdir(parents=True,exist_ok=True)
        state.write_text(json.dumps(previous,indent=2))
        for section, values in changes.items(): data.setdefault(section,{}).update(values)
    saved = backup(path)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    if restore: state.unlink()
    return {'path':str(path),'backup':str(saved),'message':'Configuração salva; o Caelestia observa o JSON sem reiniciar.'}
