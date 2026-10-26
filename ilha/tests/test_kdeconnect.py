import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from kdeconnect_monitor import DEVICE, Monitor, device_record


class KdeConnectTests(unittest.TestCase):
    def test_battery_unknown_is_not_zero_and_out_of_range_is_hidden(self):
        props = {'name': 'Meu celular', 'isPaired': True, 'isReachable': True}
        self.assertIsNone(device_record('phone', props)['charge'])
        self.assertIsNone(device_record('phone', props, {'hasBattery': True, 'charge': 101})['charge'])
        record = device_record('phone', props, {'hasBattery': True, 'charge': 0, 'isCharging': True})
        self.assertEqual(record['charge'], 0)
        self.assertTrue(record['charging'])

    def test_call_requires_paired_reachable_device_and_actual_exported_event(self):
        monitor = Monitor(None, None)
        events = []
        monitor.emit = lambda kind, **data: events.append((kind, data))
        path = '/modules/kdeconnect/devices/test/telephony'
        monitor.signal('callReceived', '123', 'Contato', path=path, member='callReceived')
        self.assertEqual(events, [])
        monitor.devices['test'] = {'paired': True, 'reachable': True}
        monitor.signal('ringing', '123', 'Contato', path=path, member='callReceived')
        self.assertEqual(events, [])
        monitor.signal('callReceived', '123', 'Contato <literal>', path=path, member='callReceived')
        self.assertEqual(events[0][1]['contact'], 'Contato <literal>')
        monitor.signal('missedCall', '123', '', path=path, member='callReceived')
        self.assertEqual(events[-1][1]['contact'], '123')

    def test_notifications_bound_text_and_do_not_accept_paths(self):
        monitor = Monitor(None, None)
        events = []
        monitor.emit = lambda kind, **data: events.append((kind, data))
        monitor.properties = lambda path, interface: {'title': 'x' * 500, 'text': 'z' * 2000,
                                                       'appName': 'App', 'silent': True}
        monitor.notice('test', '../outside')
        self.assertEqual(events, [])
        monitor.notice('test', '1')
        self.assertEqual(len(events[0][1]['title']), 200)
        self.assertEqual(len(events[0][1]['text']), 1000)
        self.assertTrue(events[0][1]['silent'])


if __name__ == '__main__':
    unittest.main()
