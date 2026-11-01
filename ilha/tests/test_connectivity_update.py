import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import connectivity_service as radio
import update_shell as update
import install_shell as installer
import desktop_cli


class ConnectivityTests(unittest.TestCase):
    def setUp(self):self.events=[];self.service=radio.Service(MagicMock(),self.events.append)
    def test_password_is_only_in_dbus_settings_and_profile_is_user_scoped(self):
        settings=radio.connection_settings(b'Teste','wpa-psk','senha-teste-123',True)
        self.assertEqual(settings['802-11-wireless-security']['psk'],'senha-teste-123')
        self.assertTrue(str(settings['connection']['permissions'][0]).startswith('user:'))
        self.assertEqual(bytes(settings['802-11-wireless']['ssid']),b'Teste')
        with self.assertRaises(ValueError):radio.connection_settings(b'Teste','wpa-psk','curta')
        self.assertEqual(radio.connection_settings(b'Teste','sae','x')['802-11-wireless-security']['key-mgmt'],'sae')
        with self.assertRaises(ValueError):radio.connection_settings(b'Teste','enterprise','secreto')
    def test_security_flags_and_no_secret_in_error(self):
        for flags,expected in [(0x100,'wpa-psk'),(0x400,'sae'),(0x200,'enterprise'),(0x800,'owe')]:
            self.assertEqual(radio.security({'RsnFlags':flags}),expected)
        self.assertEqual(radio.security({}),'open')
        self.assertNotIn('SEGREDO',radio.error_text(RuntimeError('SEGREDO')))
    def test_pairing_never_accepts_unsolicited_requests_or_wrong_confirmation(self):
        reply=MagicMock();error=MagicMock();self.service.challenge('/other','confirm','123456',reply,error)
        error.assert_called_once();reply.assert_not_called()
        self.service.pairing='/selected';self.service.challenge('/selected','confirm','123456',reply,error)
        with self.assertRaises(ValueError):self.service.answer({'id':999,'accept':True})
        reply.assert_not_called()
        self.service.answer({'id':self.service.challenge_id,'accept':False});reply.assert_not_called()
    def test_pin_passkey_and_cancel_are_explicit(self):
        self.service.pairing='/selected'
        reply=MagicMock();error=MagicMock()
        self.service.challenge('/selected','passkey','',reply,error)
        self.service.answer({'id':self.service.challenge_id,'accept':True,'value':'001234'})
        reply.assert_called_once_with(1234)
        self.service.challenge('/selected','pin','',reply,error);self.service.reject();self.assertIsNone(self.service.pending)
        error.assert_called_once()
    def test_only_our_discovery_is_stopped(self):
        self.service.discovery={'/adapter-one'};api=MagicMock()
        with patch.object(self.service,'interface',return_value=api) as interface:
            self.service.stop_discovery();interface.assert_called_once_with(radio.BLUE,'/adapter-one','org.bluez.Adapter1')
            api.StopDiscovery.assert_called_once();self.assertFalse(self.service.discovery)
    def test_wifi_disconnect_checks_selected_active_ap_and_not_ethernet(self):
        self.service.aps={'/ap':{'device':'/wifi','ssid':b'Teste','mode':'open','profiles':[]}}
        with patch.object(self.service,'wifi_state'),patch.object(self.service,'properties',return_value={'ActiveAccessPoint':'/different'}),patch.object(self.service,'interface') as interface:
            with self.assertRaisesRegex(ValueError,'ativa'):self.service.dispatch({'action':'wifi-disconnect','id':'/ap'})
            interface.assert_not_called()
    def test_saved_wifi_uses_profile_without_getting_password(self):
        self.service.aps={'/ap':{'device':'/wifi','ssid':b'Teste','mode':'wpa-psk','profiles':['/saved']}}
        api=MagicMock()
        with patch.object(self.service,'wifi_state'),patch.object(self.service,'nm',return_value=api),patch.object(self.service,'snapshot'):
            self.service.dispatch({'action':'wifi-connect','id':'/ap','password':''})
            self.assertEqual(api.ActivateConnection.call_args.args,('/saved','/wifi','/ap'))
            api.AddAndActivateConnection2.assert_not_called()
    def test_forget_requires_confirmation_and_bad_action_cannot_execute(self):
        self.service.aps={'/ap':{'device':'/wifi','profiles':['/saved']}}
        with patch.object(self.service,'wifi_state'),patch.object(self.service,'interface') as interface:
            with self.assertRaises(ValueError):self.service.dispatch({'action':'wifi-forget','id':'/ap'})
            with self.assertRaises(ValueError):self.service.dispatch({'action':'exec touch arquivo'})
            interface.assert_not_called()
    def test_blue_actions_use_selected_device_and_pairing_does_not_replace_default_agent(self):
        service=self.service;service.devices={'/device':{'Adapter':'/adapter','Paired':True}}
        api=MagicMock()
        for name in ('Pair','Connect','Disconnect'):
            getattr(api,name).side_effect=lambda *args,**kwargs:kwargs['reply_handler']()
        with patch.object(service,'blue_state',return_value={'available':True}),patch.object(service,'interface',return_value=api),patch.object(radio,'PairingAgent'):
            for action in ('blue-connect','blue-disconnect','blue-pair'):
                service.dispatch({'action':action,'id':'/device'})
            api.RegisterAgent.assert_called_once_with(radio.AGENT,'KeyboardDisplay',timeout=3)
            api.RequestDefaultAgent.assert_not_called()
            service.dispatch({'action':'blue-trust','id':'/device','enabled':True})
            self.assertEqual(api.Set.call_args.args,('org.bluez.Device1','Trusted',True))
            with self.assertRaises(ValueError):service.dispatch({'action':'blue-forget','id':'/device'})
            service.dispatch({'action':'blue-forget','id':'/device','confirmed':True})
            api.RemoveDevice.assert_called_once_with('/device',timeout=3)
    def test_new_wifi_uses_volatile_profile_when_not_saved(self):
        self.service.aps={'/ap':{'device':'/wifi','ssid':b'Teste','mode':'wpa-psk','profiles':[]}}
        api=MagicMock()
        with patch.object(self.service,'wifi_state'),patch.object(self.service,'nm',return_value=api),patch.object(self.service,'snapshot'):
            self.service.dispatch({'action':'wifi-connect','id':'/ap','password':'senha-teste-123','save':False})
            args=api.AddAndActivateConnection2.call_args.args
            self.assertEqual(args[3]['persist'],'volatile')
            self.assertEqual(args[0]['802-11-wireless-security']['psk'],'senha-teste-123')
            self.assertFalse(args[0]['connection']['autoconnect'])


class UpdateTests(unittest.TestCase):
    def package(self,invalid=None):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as archive:
            if invalid:
                entry=tarfile.TarInfo(invalid);entry.size=1;archive.addfile(entry,io.BytesIO(b'x'))
            else:
                for name in ('ilha/shell.qml','ilha/scripts/install_shell.py','install.sh','install-system.sh'):
                    entry=tarfile.TarInfo('ilha-shell/'+name);entry.size=1;archive.addfile(entry,io.BytesIO(b'x'))
        blob=data.getvalue();return blob,(hashlib.sha256(blob).hexdigest()+'  ilha-shell-abcdef1.tar.gz\n').encode()
    def test_checksum_and_archive_paths_are_checked_before_install(self):
        with tempfile.TemporaryDirectory() as temp:
            blob,checksum=self.package()
            with self.assertRaisesRegex(ValueError,'SHA-256'):update.extract_verified(blob+b'bad',checksum,'ilha-shell-abcdef1.tar.gz',temp)
            self.assertFalse(list(Path(temp).iterdir()))
            blob,checksum=self.package('ilha-shell/../../outside')
            with self.assertRaises(ValueError):update.extract_verified(blob,checksum,'ilha-shell-abcdef1.tar.gz',temp)
            blob,checksum=self.package()
            self.assertTrue((update.extract_verified(blob,checksum,'ilha-shell-abcdef1.tar.gz',temp)/'ilha/shell.qml').exists())
    def test_latest_only_accepts_own_asset_and_checksum(self):
        release={'tag_name':'v2.0.0','assets':[{'name':name,'browser_download_url':'https://github.com/'+update.REPOSITORY+'/releases/download/v2.0.0/'+name} for name in ('ilha-shell-abcdef1.tar.gz','ilha-shell-abcdef1.tar.gz.sha256')]}
        with patch.object(update,'download',return_value=json.dumps(release).encode()):self.assertEqual(update.latest()['tag'],'v2.0.0')
        release['assets'][0]['browser_download_url']='https://example.org/asset'
        with patch.object(update,'download',return_value=json.dumps(release).encode()):
            with self.assertRaises(ValueError):update.latest()
    def test_check_is_readonly_and_git_checkout_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(update,'SOURCE',Path(temp)),patch.object(update,'latest',return_value={'tag':'v2.0.0'}),patch.object(update,'download') as fetch,patch.object(update.subprocess,'run') as install,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            (Path(temp)/'.git').mkdir()
            self.assertEqual(update.main(check=True),0);self.assertEqual(update.main(),1)
            fetch.assert_not_called();install.assert_not_called()
    def test_up_to_date_install_does_not_download_or_reload(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(update,'SOURCE',Path(temp)),patch.object(update,'latest',return_value={'tag':'v2.0.0'}),patch.object(update,'git_checkout',return_value=False),patch.object(update,'download') as fetch,contextlib.redirect_stdout(io.StringIO()):
            (Path(temp)/update.RECEIPT).write_text(json.dumps({'release':'v2.0.0'}))
            self.assertEqual(update.main(),0);fetch.assert_not_called()
    def test_update_deploys_with_backup_and_receipt_without_touching_preferences(self):
        blob,checksum=self.package()
        release={'tag':'v2.0.0','name':'ilha-shell-abcdef1.tar.gz','archive':'archive','checksum':'checksum'}
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);config=home/'.config';target=config/'quickshell/ilha';target.mkdir(parents=True)
            (target/'shell.qml').write_text('versao antiga')
            preferences=config/'ilha/config.json';preferences.parent.mkdir();preferences.write_text('preferencias pessoais')
            def deploy(args,**kwargs):
                self.assertIn('--user',args);self.assertIn('--non-interactive',args)
                source=Path(args[1]).parents[1]
                with patch.object(installer,'SOURCE',source):installer.install('user')
            with patch.dict(os.environ,HOME=temp,XDG_CONFIG_HOME=str(config)),patch.object(update,'SOURCE',target),patch.object(update,'git_checkout',return_value=False),patch.object(update,'latest',return_value=release),patch.object(update,'download',side_effect=[blob,checksum]),patch.object(update.sys.stdin,'isatty',return_value=True),patch('builtins.input',return_value='sim'),patch.object(update.subprocess,'run',side_effect=deploy),patch.object(desktop_cli,'running',return_value=False),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(update.main(),0)
            self.assertEqual((target/'shell.qml').read_text(),'x')
            self.assertEqual(json.loads((target/update.RECEIPT).read_text())['release'],'v2.0.0')
            self.assertEqual(preferences.read_text(),'preferencias pessoais')
            backup=next(target.parent.glob('ilha.bak.ilha-*'))
            self.assertEqual((backup/'shell.qml').read_text(),'versao antiga')


if __name__=='__main__':unittest.main()
