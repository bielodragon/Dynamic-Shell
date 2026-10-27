import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import app_events
import app_integrations as apps
from app_sources import vdf,DownloadTracker,steam_games,instances
from app_streams import LocalSendParser,MinecraftParser


class AppTests(unittest.TestCase):
    def test_vdf_rejects_partial_and_handles_comments(self):
        self.assertEqual(vdf('// teste\n"root" { "nome" "Um \\"jogo\\"" }'),{'root':{'nome':'Um "jogo"'}})
        for data in ('"root" { "nome" "jogo"','"root"','}'):
            with self.assertRaises(ValueError):vdf(data)

    def test_download_requires_advancing_counters_and_running_client(self):
        tracker=DownloadTracker()
        def sample(done,running=True,now=0):return tracker.sample([dict(id='42',name='Teste',downloaded=done,total=100)],running,now)
        self.assertEqual(sample(20),[])
        self.assertEqual(sample(30,now=2)[0]['progress'],30)
        self.assertEqual(sample(30,now=4)[0]['detail'],'Aguardando atualização dos contadores')
        self.assertEqual(sample(30,now=18),[])
        self.assertEqual(sample(100,now=20)[0]['state'],'success')
        self.assertEqual(sample(100,now=22),[])
        self.assertEqual(sample(110,False,24),[])

    def test_catalogs_keep_only_public_metadata_and_safe_launch_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);steam=root/'Steam';(steam/'steamapps').mkdir(parents=True)
            (steam/'steamapps/appmanifest_42.acf').write_text('"AppState" { "appid" "42" "name" "Jogo $(literal)" "LastOwner" "PRIVADO" "BytesDownloaded" "10" "BytesToDownload" "20" }')
            prism=root/'PrismLauncher';instance=prism/'instances/Meu jogo';instance.mkdir(parents=True)
            cfg=instance/'instance.cfg';cfg.write_text('[General]\nname=Meu mundo\nWrapperCommand=\nPreLaunchCommand=\nPostExitCommand=\nOverrideCommands=false\n')
            wrapper=root/'.local/bin/ilha-minecraft';wrapper.parent.mkdir(parents=True);wrapper.touch()
            with patch.dict(os.environ,HOME=temp,XDG_DATA_HOME=temp,ILHA_STEAM_ROOT=str(steam),ILHA_PRISM_ROOT=str(prism)):
                games=steam_games();self.assertEqual(len(games),1);self.assertNotIn('PRIVADO',json.dumps(games))
                item=instances()[0];self.assertEqual(len(item['id']),24)
                with patch.object(apps.shutil,'which',return_value='/bin/steam'),patch.object(apps.subprocess,'Popen') as popen:
                    apps.launch('steam','42');self.assertEqual(popen.call_args.args[0],['/bin/steam','steam://rungameid/42'])
                    with self.assertRaises(ValueError):apps.launch('steam','42;bad')
                before=cfg.read_text();apps.setup_minecraft(item['id']);self.assertEqual(cfg.read_text(),before)
                result=apps.setup_minecraft(item['id'],True);self.assertEqual(Path(result['backup']).read_text(),before)
                self.assertIn('OverrideCommands=true',cfg.read_text())
                self.assertNotIn('backup',apps.setup_minecraft(item['id'],True))
                cfg.write_text(before.replace('WrapperCommand=','WrapperCommand=echo ilha-minecraft '))
                with self.assertRaisesRegex(ValueError,'personalizados'):apps.setup_minecraft(item['id'],True)

    def test_localsend_fragmented_status_and_no_private_labels(self):
        reader=LocalSendParser();data='\x1b[1GS dispositivo-secreto [##--] 1.0 MB / 4.0 MB [1 MB/s] [ETA: 3s]\r\n'.encode()
        events=[]
        for char in data:events+=reader.feed(bytes([char]))
        self.assertEqual(events[0][1]['progress'],25)
        self.assertNotIn('dispositivo-secreto',str(events))
        done=reader.feed(b'S privado: Sent 1 file (4 MB, took 2s)\n')
        self.assertTrue(done[0][2]);self.assertEqual(done[0][1]['state'],'success')
        failed=reader.feed(b'R privado: Received 2 files (4 MB, took 2s), 1 failed\n')
        self.assertEqual(failed[0][1]['state'],'error');self.assertIsNone(failed[0][1]['progress'])
        cancelled=reader.feed(b'S privado: Declined\n');self.assertEqual(cancelled[0][1]['state'],'paused')
        self.assertEqual(reader.feed(b'process exited 0\n'),[])

    def test_minecraft_does_not_echo_chat_or_server(self):
        reader=MinecraftParser();self.assertIsNone(reader.feed(b'[CHAT] segredo\n'))
        self.assertEqual(reader.feed(b'Connecting to servidor-privado\n'),'Conectando ao servidor')

    def test_events_disable_expire_and_do_not_depend_on_shell(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,XDG_RUNTIME_DIR=temp),patch.object(app_events,'config',return_value={}):
            reporter=app_events.Reporter('minecraft');reporter.emit('Teste')
            self.assertEqual(len(app_events.read_events({})),1)
            self.assertEqual(app_events.read_events({'minecraft':False}),[])
            with patch.object(app_events,'config',return_value={'integrations':{'minecraft':False}}):reporter.emit('Teste')
            self.assertFalse(reporter.path.exists())
            reporter.emit('Final',state='success',final=True)
            with patch.object(app_events.time,'time',return_value=reporter.last+9):self.assertEqual(app_events.read_events({}),[])


if __name__=='__main__':unittest.main()
