#!/usr/bin/env python3
"""NetworkManager/BlueZ via D-Bus. Senhas só passam por stdin e pela API do NM."""
import getpass
import json
import os
import re
import signal
import sys
import time
import uuid
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

NM='org.freedesktop.NetworkManager'
BASE='/org/freedesktop/NetworkManager'
BLUE='org.bluez'
PROPS='org.freedesktop.DBus.Properties'
AGENT='/org/ilha/PairingAgent'


def security(ap):
    flags=int(ap.get('WpaFlags',0))|int(ap.get('RsnFlags',0))
    if flags&0x100:return 'wpa-psk'
    if flags&0x400:return 'sae'
    if flags&(0x200|0x2000):return 'enterprise'
    if flags&(0x800|0x1000):return 'owe'
    return 'wep' if int(ap.get('Flags',0))&1 else 'open'


def connection_settings(ssid,mode,password,save=True):
    if not isinstance(password,str) or len(password)>1024 or '\0' in password:raise ValueError('Senha inválida.')
    if mode in ('enterprise','wep'):raise ValueError('Use um perfil já configurado no NetworkManager para WEP/802.1X.')
    if mode=='wpa-psk' and not (8<=len(password)<=63 or re.fullmatch(r'[a-fA-F0-9]{64}',password)):raise ValueError('WPA pessoal exige 8–63 caracteres ou 64 dígitos hexadecimais.')
    if mode=='sae' and not password:raise ValueError('Informe a senha WPA3.')
    value={'connection':{'id':ssid.decode('utf-8','replace')[:120],'uuid':str(uuid.uuid4()),'type':'802-11-wireless',
        'permissions':dbus.Array(['user:'+getpass.getuser()+':'],signature='s'),'autoconnect':dbus.Boolean(save)},
        '802-11-wireless':{'ssid':dbus.ByteArray(ssid),'mode':'infrastructure'},
        'ipv4':{'method':'auto'},'ipv6':{'method':'auto'}}
    if mode!='open':
        value['802-11-wireless-security']={'key-mgmt':mode}
        if mode!='owe':value['802-11-wireless-security']['psk']=password
    return dbus.Dictionary({key:dbus.Dictionary(fields,signature='sv') for key,fields in value.items()},signature='sa{sv}')


def error_text(error):
    # Erros não replicam argumentos, senha, dump D-Bus ou saídas brutas.
    name=error.get_dbus_name() if isinstance(error,dbus.DBusException) else ''
    if 'NotAuthorized' in name or 'AccessDenied' in name:return 'Permissão recusada pelo sistema. Confira o agente Polkit.'
    if 'NotReady' in name:return 'Adaptador desligado ou indisponível.'
    if 'Authentication' in name:return 'Autenticação/pareamento recusado. Confira a senha ou código.'
    if 'InProgress' in name:return 'Já existe uma operação em andamento.'
    if isinstance(error,ValueError):return str(error)[:240]
    return 'Não foi possível concluir a operação. Confira o dispositivo ou o serviço do sistema.'


class Rejected(dbus.DBusException):_dbus_error_name='org.bluez.Error.Rejected'


class PairingAgent(dbus.service.Object):
    def __init__(self,service):self.service=service;super().__init__(service.bus,AGENT)
    @dbus.service.method('org.bluez.Agent1',in_signature='',out_signature='')
    def Release(self):self.service.reject()
    @dbus.service.method('org.bluez.Agent1',in_signature='o',out_signature='s',async_callbacks=('reply','error'))
    def RequestPinCode(self,device,reply,error):self.service.challenge(device,'pin','',reply,error)
    @dbus.service.method('org.bluez.Agent1',in_signature='o',out_signature='u',async_callbacks=('reply','error'))
    def RequestPasskey(self,device,reply,error):self.service.challenge(device,'passkey','',reply,error)
    @dbus.service.method('org.bluez.Agent1',in_signature='ou',out_signature='',async_callbacks=('reply','error'))
    def RequestConfirmation(self,device,passkey,reply,error):self.service.challenge(device,'confirm',f'{int(passkey):06d}',reply,error)
    @dbus.service.method('org.bluez.Agent1',in_signature='o',out_signature='',async_callbacks=('reply','error'))
    def RequestAuthorization(self,device,reply,error):self.service.challenge(device,'authorize','',reply,error)
    @dbus.service.method('org.bluez.Agent1',in_signature='os',out_signature='',async_callbacks=('reply','error'))
    def AuthorizeService(self,device,service_uuid,reply,error):self.service.challenge(device,'authorize','',reply,error)
    @dbus.service.method('org.bluez.Agent1',in_signature='os',out_signature='')
    def DisplayPinCode(self,device,pincode):self.service.display(device,str(pincode))
    @dbus.service.method('org.bluez.Agent1',in_signature='ouq',out_signature='')
    def DisplayPasskey(self,device,passkey,entered):self.service.display(device,f'{int(passkey):06d} · {int(entered)} teclas')
    @dbus.service.method('org.bluez.Agent1',in_signature='',out_signature='')
    def Cancel(self):self.service.reject()


class Service:
    def __init__(self,bus,emit):
        self.bus=bus;self.emit=emit;self.mode='wifi';self.busy=False;self.message=''
        self.aps={};self.devices={};self.adapters={};self.profiles={};self.wifi_devices={}
        self.discovery=set();self.agent=None;self.pairing=None;self.pending=None;self.challenge_id=0;self.closed=False
        self.activation=None
    def interface(self,name,path,interface):return dbus.Interface(self.bus.get_object(name,path),interface)
    def properties(self,name,path,interface):return self.interface(name,path,PROPS).GetAll(interface,timeout=2)
    def nm(self):return self.interface(NM,BASE,NM)
    def saved(self):
        result={}
        for path in self.interface(NM,BASE+'/Settings',NM+'.Settings').ListConnections(timeout=2):
            try:
                settings=self.interface(NM,path,NM+'.Settings.Connection').GetSettings(timeout=2)
                if settings.get('connection',{}).get('type')=='802-11-wireless':result[str(path)]=settings
            except dbus.DBusException:pass
        self.profiles=result
    def wifi_state(self):
        flags=self.properties(NM,BASE,NM);self.saved();self.aps={};self.wifi_devices={};rows={}
        for path in self.nm().GetDevices(timeout=2):
            device=self.properties(NM,path,NM+'.Device')
            if int(device['DeviceType'])!=2:continue
            device_id=str(path);self.wifi_devices[device_id]=device
            if self.activation and self.activation[0]==device_id:
                if int(device['State'])==100:self.activation=None
                elif int(device['State'])==120 or time.monotonic()-self.activation[1]>65:
                    self.activation=None;self.message='A conexão Wi-Fi não foi concluída. Confira a senha, o sinal e as permissões.'
            wifi=self.properties(NM,path,NM+'.Device.Wireless');active=str(wifi.get('ActiveAccessPoint','/'))
            for ap_path in self.interface(NM,path,NM+'.Device.Wireless').GetAllAccessPoints(timeout=2):
                try:ap=self.properties(NM,ap_path,NM+'.AccessPoint')
                except dbus.DBusException:continue
                ssid=bytes(ap.get('Ssid',b''))
                if not ssid:continue
                mode=security(ap);key=(device_id,ssid,mode)
                compatible=[str(value) for value in device.get('AvailableConnections',[]) if str(value) in self.profiles and bytes(self.profiles[str(value)].get('802-11-wireless',{}).get('ssid',b''))==ssid]
                item={'id':str(ap_path),'ssid':ssid.decode('utf-8','replace'),'interface':str(device['Interface']),
                    'device':device_id,'strength':int(ap['Strength']),'security':mode,'connected':str(ap_path)==active and int(device['State'])==100,
                    'connecting':str(ap_path)==active and 40<=int(device['State'])<100,'saved':bool(compatible)}
                self.aps[str(ap_path)]={'device':device_id,'ssid':ssid,'mode':mode,'profiles':compatible}
                previous=rows.get(key)
                if previous is None or item['connected'] or (not previous['connected'] and item['strength']>previous['strength']):rows[key]=item
        return {'available':bool(self.wifi_devices),'enabled':bool(flags['WirelessEnabled']),'hardware':bool(flags['WirelessHardwareEnabled']),
            'networks':sorted(rows.values(),key=lambda item:(not item['connected'],-item['strength'],item['ssid'].casefold()))}
    def blue_state(self):
        objects=self.interface(BLUE,'/','org.freedesktop.DBus.ObjectManager').GetManagedObjects(timeout=2)
        self.adapters={str(path):fields['org.bluez.Adapter1'] for path,fields in objects.items() if 'org.bluez.Adapter1' in fields}
        self.devices={str(path):fields['org.bluez.Device1'] for path,fields in objects.items() if 'org.bluez.Device1' in fields}
        rows=[]
        for path,fields in self.devices.items():
            battery=objects.get(dbus.ObjectPath(path),{}).get('org.bluez.Battery1',{}).get('Percentage')
            rows.append({'id':path,'name':str(fields.get('Alias',fields.get('Name','Dispositivo Bluetooth'))),
                'connected':bool(fields.get('Connected')),'paired':bool(fields.get('Paired')),'trusted':bool(fields.get('Trusted')),
                'blocked':bool(fields.get('Blocked')),'battery':int(battery) if battery is not None else None})
        return {'available':bool(self.adapters),'enabled':any(bool(a.get('Powered')) for a in self.adapters.values()),
            'discovering':bool(self.discovery),'devices':sorted(rows,key=lambda item:(not item['connected'],not item['paired'],item['name'].casefold()))}
    def snapshot(self):
        if self.closed:return False
        try:state=self.wifi_state() if self.mode=='wifi' else self.blue_state()
        except Exception:state={'available':False,'error':'Serviço ou adaptador indisponível.'}
        self.emit({'type':'state','mode':self.mode,'state':state,'busy':self.busy,'message':self.message})
        return True
    def done(self,*_):
        self.busy=False;self.pairing=None;self.reject();self.snapshot()
    def failed(self,error):self.activation=None;self.message=error_text(error);self.done()
    def async_call(self,function,*args,reply=None):
        self.busy=True
        try:function(*args,reply_handler=reply or self.done,error_handler=self.failed,timeout=65)
        except Exception:self.busy=False;raise
    def stop_discovery(self):
        for path in list(self.discovery):
            try:self.interface(BLUE,path,'org.bluez.Adapter1').StopDiscovery(timeout=2)
            except dbus.DBusException:pass
            self.discovery.discard(path)
        return False
    def challenge(self,device,kind,code,reply,error):
        if str(device)!=self.pairing or self.pending:error(Rejected('Pareamento não solicitado.'));return
        self.challenge_id+=1;self.pending=(kind,reply,error)
        self.emit({'type':'challenge','id':self.challenge_id,'kind':kind,'code':code,'device':str(self.devices.get(str(device),{}).get('Alias','Dispositivo'))})
    def display(self,device,code):
        if str(device)!=self.pairing:raise Rejected('Pareamento não solicitado.')
        self.emit({'type':'challenge','id':0,'kind':'display','code':code,'device':str(self.devices.get(str(device),{}).get('Alias','Dispositivo'))})
    def reject(self):
        if self.pending:
            _,_,error=self.pending;self.pending=None;error(Rejected('Cancelado pelo usuário.'))
        self.emit({'type':'challenge','kind':''})
    def answer(self,payload):
        if not self.pending or payload.get('id')!=self.challenge_id:raise ValueError('Confirmação de pareamento expirada.')
        kind,reply,error=self.pending;self.pending=None
        if payload.get('accept') is not True:error(Rejected('Recusado pelo usuário.'))
        elif kind=='pin':
            value=payload.get('value','')
            if not isinstance(value,str) or not 1<=len(value)<=16:error(Rejected('PIN inválido.'))
            else:reply(value)
        elif kind=='passkey':
            value=payload.get('value','')
            if not isinstance(value,str) or not re.fullmatch(r'\d{1,6}',value):error(Rejected('Código inválido.'))
            else:reply(dbus.UInt32(int(value)))
        else:reply()
        self.emit({'type':'challenge','kind':''})
    def dispatch(self,payload):
        name=payload.get('action');self.message=''
        if name=='answer':self.answer(payload);return
        if name=='cancel-pair':
            if self.pairing:self.interface(BLUE,self.pairing,'org.bluez.Device1').CancelPairing(timeout=2)
            self.reject();return
        if name=='mode':
            if payload.get('mode') not in ('wifi','bluetooth'):raise ValueError('Painel inválido.')
            self.stop_discovery();self.mode=payload['mode'];self.snapshot();return
        if name=='refresh':self.snapshot();return
        if self.busy:raise ValueError('Aguarde a operação atual.')
        if name=='wifi-scan':
            self.wifi_state()
            for path in self.wifi_devices:self.interface(NM,path,NM+'.Device.Wireless').RequestScan(dbus.Dictionary({},signature='sv'),timeout=3)
        elif name=='wifi-power':
            if type(payload.get('enabled')) is not bool:raise ValueError('Estado inválido.')
            self.interface(NM,BASE,PROPS).Set(NM,'WirelessEnabled',dbus.Boolean(payload['enabled']),timeout=3)
        elif name in ('wifi-connect','wifi-disconnect','wifi-forget'):
            self.wifi_state();item=self.aps.get(payload.get('id'))
            if not item:raise ValueError('A rede não está mais disponível. Atualize a lista.')
            if name=='wifi-disconnect':
                wifi=self.properties(NM,item['device'],NM+'.Device.Wireless')
                if str(wifi.get('ActiveAccessPoint','/'))!=payload['id']:raise ValueError('A rede selecionada não é a conexão ativa.')
                self.async_call(self.interface(NM,item['device'],NM+'.Device').Disconnect)
            elif name=='wifi-forget':
                if payload.get('confirmed') is not True:raise ValueError('Confirme antes de esquecer a rede.')
                for path in item['profiles']:self.interface(NM,path,NM+'.Settings.Connection').Delete(timeout=3)
            else:
                password=payload.get('password','')
                if item['profiles'] and not password:
                    self.activation=(item['device'],time.monotonic())
                    self.async_call(self.nm().ActivateConnection,dbus.ObjectPath(item['profiles'][0]),dbus.ObjectPath(item['device']),dbus.ObjectPath(payload['id']))
                else:
                    save=payload.get('save',True)
                    if type(save) is not bool:raise ValueError('Estado inválido.')
                    settings=connection_settings(item['ssid'],item['mode'],password,save)
                    self.activation=(item['device'],time.monotonic())
                    self.async_call(self.nm().AddAndActivateConnection2,settings,dbus.ObjectPath(item['device']),dbus.ObjectPath(payload['id']),dbus.Dictionary({'persist':'disk' if save else 'volatile'},signature='sv'))
        elif name=='blue-power':
            if type(payload.get('enabled')) is not bool:raise ValueError('Estado inválido.')
            self.blue_state();self.stop_discovery()
            for path in self.adapters:self.interface(BLUE,path,PROPS).Set('org.bluez.Adapter1','Powered',dbus.Boolean(payload['enabled']),timeout=3)
        elif name=='blue-scan':
            self.blue_state()
            for path,fields in self.adapters.items():
                if fields.get('Powered') and path not in self.discovery:
                    self.interface(BLUE,path,'org.bluez.Adapter1').StartDiscovery(timeout=3);self.discovery.add(path)
            GLib.timeout_add_seconds(30,self.stop_discovery)
        elif name.startswith('blue-'):
            self.blue_state();path=payload.get('id');fields=self.devices.get(path)
            if not fields:raise ValueError('Dispositivo não encontrado.')
            device=self.interface(BLUE,path,'org.bluez.Device1')
            if name=='blue-connect':
                if not fields.get('Paired'):raise ValueError('Pareie o dispositivo primeiro.')
                self.async_call(device.Connect)
            elif name=='blue-disconnect':self.async_call(device.Disconnect)
            elif name=='blue-pair':
                if not self.agent:
                    self.agent=PairingAgent(self)
                    try:self.interface(BLUE,'/org/bluez','org.bluez.AgentManager1').RegisterAgent(AGENT,'KeyboardDisplay',timeout=3)
                    except Exception:self.agent.remove_from_connection();self.agent=None;raise
                self.pairing=path
                self.async_call(device.Pair,reply=lambda:self.async_call(device.Connect))
            elif name in ('blue-trust','blue-block'):
                if type(payload.get('enabled')) is not bool:raise ValueError('Estado inválido.')
                self.interface(BLUE,path,PROPS).Set('org.bluez.Device1','Trusted' if name=='blue-trust' else 'Blocked',dbus.Boolean(payload['enabled']),timeout=3)
            elif name=='blue-forget':
                if payload.get('confirmed') is not True:raise ValueError('Confirme antes de remover o pareamento.')
                self.interface(BLUE,str(fields['Adapter']),'org.bluez.Adapter1').RemoveDevice(dbus.ObjectPath(path),timeout=3)
            else:raise ValueError('Ação desconhecida.')
        else:raise ValueError('Ação desconhecida.')
        self.snapshot()
    def close(self):
        self.closed=True;self.stop_discovery()
        if self.pairing:
            try:self.interface(BLUE,self.pairing,'org.bluez.Device1').CancelPairing(timeout=2)
            except dbus.DBusException:pass
        self.reject()
        if self.agent:
            try:self.interface(BLUE,'/org/bluez','org.bluez.AgentManager1').UnregisterAgent(AGENT,timeout=2)
            except dbus.DBusException:pass


def main():
    DBusGMainLoop(set_as_default=True);loop=GLib.MainLoop()
    emit=lambda data:print(json.dumps(data,ensure_ascii=False),flush=True)
    service=Service(dbus.SystemBus(),emit);pending=b''
    def read(*_):
        nonlocal pending
        data=os.read(sys.stdin.fileno(),4096)
        if not data:loop.quit();return False
        pending+=data
        if len(pending)>16384:pending=b'';emit({'type':'error','message':'Pedido grande demais.'});return True
        while b'\n' in pending:
            line,pending=pending.split(b'\n',1)
            try:
                value=json.loads(line)
                if not isinstance(value,dict):raise ValueError('Pedido inválido.')
                service.dispatch(value)
            except Exception as error:emit({'type':'error','message':error_text(error)})
        return True
    GLib.io_add_watch(sys.stdin,GLib.IO_IN|GLib.IO_HUP,read)
    GLib.timeout_add_seconds(4,service.snapshot)
    def stop():loop.quit();return False
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,stop)
    service.snapshot()
    try:loop.run()
    finally:service.close()


if __name__=='__main__':main()
