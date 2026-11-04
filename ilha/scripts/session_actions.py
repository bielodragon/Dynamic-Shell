"""Seleciona ações pela sessão ativa, sem iniciar outros shells."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def probe(args):
    try:
        result=subprocess.run(args,capture_output=True,text=True,timeout=3)
        return result.stdout.strip() if result.returncode==0 else None
    except (OSError,subprocess.SubprocessError):return None


def lock_plan():
    candidates=[]
    for executable,prefix,provider in [('caelestia',['shell','lock'],'Caelestia'),('omarchy-shell',['lock'],'Omarchy')]:
        path=shutil.which(executable)
        if not path:continue
        state=probe([path,*prefix,'isLocked'])
        if state not in ('true','false'):continue
        candidates.append({'provider':provider,'command':[path,*prefix,'lock'],'detached':False,'locked':state=='true'})
    if candidates:return next((value for value in candidates if value['locked']),candidates[0])
    if os.environ.get('WAYLAND_DISPLAY'):
        for name in ('hyprlock','swaylock'):
            path=shutil.which(name)
            if path:return {'provider':name,'command':[path],'detached':True,'locked':False}
    return None


def uwsm_cgroup(text):
    # Um graphical-session.target ativo também existe em sessões sem UWSM.
    return any(part.startswith('wayland-wm@') and part.endswith('.service') for part in text.strip().split('/'))


def logout_plan():
    signature=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    hyprctl=shutil.which('hyprctl')
    if not signature or not hyprctl:return None
    try:
        version=json.loads(probe([hyprctl,'-j','version']) or '{}')
        match=re.match(r'^(\d+)\.(\d+)\.(\d+)',version.get('version',''))
        if not match:return None
        instances=json.loads(probe([hyprctl,'-j','instances']) or '[]')
        instance=next((row for row in instances if row.get('instance')==signature),None)
        if instance:
            pid=int(instance['pid'])
            if pid<=0:return None
            try:cgroup=(Path('/proc')/str(pid)/'cgroup').read_text()
            except OSError:cgroup=''
            uwsm=shutil.which('uwsm')
            if uwsm and uwsm_cgroup(cgroup):return {'provider':'UWSM','command':[uwsm,'stop'],'detached':False}
        graceful=shutil.which('hyprshutdown')
        if graceful:return {'provider':'Hyprshutdown','command':[graceful],'detached':True}
        if tuple(map(int,match.groups()))>=(0,55,0):
            # Verifica apenas o tipo, sem executar a função de saída.
            if probe([hyprctl,'eval','assert(type(hl.dsp.exit) == "function")'])!='ok':return None
            dispatch='hl.dsp.exit()'
        else:dispatch='exit'
        return {'provider':'Hyprland','command':[hyprctl,'dispatch',dispatch],'detached':False}
    except (ValueError,TypeError,KeyError):return None


def execute(plan,locking=False):
    if not plan:raise RuntimeError('Nenhum provedor de bloqueio ativo.' if locking else 'Saída indisponível nesta sessão.')
    if locking and plan.get('locked'):return
    if plan['detached']:
        child=subprocess.Popen(plan['command'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            code=child.wait(timeout=.3)
            if code:raise RuntimeError('O aplicativo encerrou com erro. Confira sua configuração de bloqueio/saída.')
        except subprocess.TimeoutExpired:pass
        return
    result=subprocess.run(plan['command'],capture_output=True,text=True,timeout=8)
    output=result.stdout.strip().lower()
    errors=('target not found','function not found','not ready','too few arguments','too many arguments','missing-pam','failed','invalid dispatcher')
    if result.returncode or any(error in output for error in errors):
        raise RuntimeError('Não foi possível solicitar o bloqueio.' if locking else 'Não foi possível solicitar a saída da sessão.')


def lock():execute(lock_plan(),locking=True)
def logout():execute(logout_plan())


if __name__=='__main__':print(json.dumps({'lock':lock_plan(),'logout':logout_plan()},ensure_ascii=False))
