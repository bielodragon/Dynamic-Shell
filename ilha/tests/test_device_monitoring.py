import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import device_metrics as metrics
import performance_mode as performance
import game_runner


class MonitoringTests(unittest.TestCase):
    def test_cpu_delta_and_first_sample(self):
        self.assertIsNone(metrics.cpu_percent(None,(100,50)))
        self.assertEqual(metrics.cpu_percent((100,50),(200,75)),75)
        self.assertIsNone(metrics.cpu_percent((200,75),(100,50)))

    def test_memory_available_and_missing_gpu(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'meminfo';path.write_text('MemTotal: 1048576 kB\nMemAvailable: 262144 kB\n')
            self.assertEqual(metrics.memory(path),{'percent':75.0,'usedGiB':.8,'totalGiB':1.0})
            self.assertEqual(metrics.gpu_usage(root),[])
            self.assertEqual(metrics.temperatures(root),{'cpu':None,'gpu':None})

    def test_battery_excludes_peripherals_and_absent_packs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertFalse(metrics.battery(root)['available'])
            for name,scope,present in [('BAT0','System','1'),('mouse','Device','1'),('BAT1','System','0')]:
                p=root/name;p.mkdir()
                for key,value in {'type':'Battery','scope':scope,'present':present,'capacity':'42','status':'Discharging'}.items(): (p/key).write_text(value)
            rows=metrics.battery(root)['batteries']
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['percent'],42)

    def test_performance_preserves_original_effects_and_external_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            state={name:True for name in performance.OPTIONS};state[performance.OPTIONS[2]]=False
            original=state.copy()
            with patch.object(performance,'state_path',return_value=Path(folder)/'state.json'), patch.object(performance,'read',side_effect=lambda k:state[k]), patch.object(performance,'set_option',side_effect=lambda k,v:state.update({k:v})):
                performance.apply(True);self.assertFalse(any(state.values()))
                performance.apply(True)  # Não perder o estado original numa segunda chamada.
                performance.apply(False);self.assertEqual(state,original)
                performance.apply(True);state[performance.OPTIONS[2]]=True
                performance.apply(False)
                self.assertTrue(state[performance.OPTIONS[2]])

    def test_performance_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as folder:
            state={name:True for name in performance.OPTIONS};calls=[]
            def change(name,value):
                calls.append((name,value))
                if len(calls)==2: raise RuntimeError('falhou')
                state[name]=value
            with patch.object(performance,'state_path',return_value=Path(folder)/'state.json'), patch.object(performance,'read',side_effect=lambda k:state[k]), patch.object(performance,'set_option',side_effect=change):
                with self.assertRaises(RuntimeError): performance.apply(True)
                self.assertTrue(all(state.values()))

    def test_game_configuration_uses_theme_and_honors_hidden_state(self):
        theme=json.loads((Path(__file__).resolve().parents[1]/'themes/nord.json').read_text())
        result=game_runner.options(theme,False,'ilha-hud-test')
        self.assertIn('no_display',result)
        self.assertIn('text_color='+theme['colors']['text'][1:],result)
        self.assertNotIn('no_display',game_runner.options(theme,True,'ilha-hud-test'))

    def test_hud_only_toggles_owned_registered_sessions(self):
        import socket
        from unittest.mock import MagicMock
        client=MagicMock();client.__enter__.return_value=client;client.recv.return_value=b':MangoHudVersion=0.8.4;'
        row={'visible':False,'socket':'ilha-hud-test'}
        with patch.object(game_runner,'sessions',return_value=[(Path('/tmp/mock.json'),row)]), patch.object(game_runner.socket,'socket',return_value=client), patch.object(game_runner,'write_json') as write:
            game_runner.set_visible(True)
            client.connect.assert_called_once_with('\0ilha-hud-test')
            client.sendall.assert_called_once_with(b':hud;')
            self.assertTrue(write.call_args.args[1]['visible'])


if __name__=='__main__': unittest.main()
