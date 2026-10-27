#!/usr/bin/env python3
"""Leituras do dispositivo; ausência de sensor é null, nunca um valor inventado."""
import argparse
import json
from pathlib import Path
import time


def battery(root=None):
    if root is None:
        try:
            import dbus
            bus = dbus.SystemBus()
            manager = dbus.Interface(bus.get_object('org.freedesktop.UPower','/org/freedesktop/UPower'),'org.freedesktop.UPower')
            path = manager.GetDisplayDevice(timeout=2)
            props = dbus.Interface(bus.get_object('org.freedesktop.UPower',path),'org.freedesktop.DBus.Properties')
            data = props.GetAll('org.freedesktop.UPower.Device',timeout=2)
            if int(data['Type']) == 2 and bool(data['IsPresent']) and bool(data['PowerSupply']):
                status = {1:'Charging',2:'Discharging',4:'Full'}.get(int(data['State']),'Unknown')
                return {'available':True,'batteries':[{'name':'Bateria','percent':round(float(data['Percentage'])),
                    'status':status,'seconds':int(data['TimeToFull'] if status=='Charging' else data['TimeToEmpty'])}]}
        except Exception: pass
    root = Path(root or '/sys/class/power_supply')
    rows = []
    for path in sorted(root.glob('*')):
        try:
            if (path/'type').read_text().strip() != 'Battery': continue
            if (path/'scope').exists() and (path/'scope').read_text().strip() == 'Device': continue
            if (path/'present').exists() and (path/'present').read_text().strip() != '1': continue
            percent = int((path/'capacity').read_text())
            if 0 <= percent <= 100:
                rows.append({'name':path.name,'percent':percent,'status':(path/'status').read_text().strip()})
        except (OSError, ValueError): pass
    return {'available':bool(rows),'batteries':rows}


def cpu_counters(path=Path('/proc/stat')):
    values = list(map(int,path.read_text().splitlines()[0].split()[1:9]))
    return sum(values), values[3] + values[4]


def cpu_percent(previous, current):
    if previous is None or current[0] <= previous[0]: return None
    return round(max(0,min(100,100 * (1-(current[1]-previous[1])/(current[0]-previous[0])))),1)


def memory(path=Path('/proc/meminfo')):
    values = {line.split(':')[0]:int(line.split()[1]) for line in path.read_text().splitlines()}
    total = values['MemTotal']; used = max(0,total-values['MemAvailable'])
    return {'percent':round(100*used/total,1),'usedGiB':round(used/1048576,1),'totalGiB':round(total/1048576,1)}


def temperatures(root=Path('/sys/class/hwmon')):
    cpu, gpu = [], []
    for device in root.glob('hwmon*'):
        try: name = (device/'name').read_text().strip()
        except OSError: continue
        group = cpu if name in ('coretemp','k10temp','zenpower','cpu_thermal') else gpu if name in ('radeon','amdgpu','i915','nouveau') else None
        if group is None: continue
        for path in device.glob('temp*_input'):
            try:
                value = int(path.read_text())/1000
                if -20 <= value <= 150: group.append(value)
            except (OSError,ValueError): pass
    return {'cpu':max(cpu) if cpu else None,'gpu':max(gpu) if gpu else None}


def gpu_usage(root=Path('/sys/class/drm')):
    values = []
    for path in root.glob('card[0-9]*/device/gpu_busy_percent'):
        try:
            value = int(path.read_text())
            if 0 <= value <= 100: values.append({'device':path.parents[1].name,'percent':value})
        except (OSError,ValueError): pass
    return values


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--metrics',action='store_true');args=parser.parse_args()
    previous = None
    while True:
        result = {'battery':battery()}
        if args.metrics:
            try:
                current = cpu_counters();result.update(cpu=cpu_percent(previous,current),memory=memory(),temperature=temperatures(),gpus=gpu_usage());previous=current
            except (OSError,ValueError,KeyError) as error: result['error']=str(error)[:150]
        print(json.dumps(result),flush=True)
        time.sleep(2 if args.metrics else 15)


if __name__ == '__main__': main()
