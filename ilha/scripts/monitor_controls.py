#!/usr/bin/env python3
import json
import shutil
import sys
import performance_mode
import game_runner


def status():
    return {'performance':performance_mode.enabled(),'mangoAvailable':bool(shutil.which('mangohud')),
            'games':len(game_runner.sessions())}


if __name__=='__main__':
    try:
        operation=sys.argv[1]
        if operation=='performance': performance_mode.apply(json.loads(sys.argv[2]))
        elif operation=='hud': game_runner.set_visible(json.loads(sys.argv[2]))
        elif operation!='status': raise ValueError('Operação desconhecida.')
        response={'ok':True,'state':status()}
    except Exception as error: response={'ok':False,'error':str(error)[:240]}
    print(json.dumps(response,ensure_ascii=False))
