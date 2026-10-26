import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from privacy_monitor import Graph
from obs_config import authentication


def node(identifier, kind, state='running', **props):
    return {'id': identifier, 'type': 'PipeWire:Interface:Node',
            'info': {'state': state, 'props': {'media.class': kind, **props}}}


def link(source, target, state='active'):
    return {'id': 90, 'type': 'PipeWire:Interface:Link', 'info': {
        'state': state, 'props': {'link.output.node': source, 'link.input.node': target}}}


class PrivacyTests(unittest.TestCase):
    def test_microphone_needs_active_capture_not_playback(self):
        graph = Graph()
        graph.update([node(1, 'Audio/Source'), node(2, 'Stream/Input/Audio')])
        self.assertFalse(graph.snapshot()['microphone'])
        graph.update([link(1, 2, 'paused')])
        self.assertFalse(graph.snapshot()['microphone'])
        graph.update([{'id': 90, 'info': {'state': 'active'}}])
        self.assertTrue(graph.snapshot()['microphone'])
        graph.update([{'id': 2, 'info': {'props': {'media.class': 'Stream/Output/Audio'}}}])
        self.assertFalse(graph.snapshot()['microphone'])

    def test_sink_monitor_is_not_microphone(self):
        graph = Graph()
        graph.update([node(1, 'Audio/Sink'), node(2, 'Stream/Input/Audio'), link(1, 2)])
        self.assertFalse(graph.snapshot()['microphone'])
        graph.update([node(1, 'Audio/Source', **{'node.name': 'output.monitor'})])
        self.assertFalse(graph.snapshot()['microphone'])

    def test_suspended_device_is_not_capture_and_partial_update_keeps_metadata(self):
        graph = Graph()
        graph.update([node(1, 'Video/Source', 'suspended', **{'media.role': 'Camera'})])
        self.assertFalse(graph.snapshot()['camera'])
        graph.update([{'id': 1, 'info': {'state': 'running'}}])
        self.assertTrue(graph.snapshot()['camera'])
        graph.update([{'id': 1, 'info': None}])
        self.assertFalse(graph.snapshot()['camera'])

    def test_screen_and_unknown_video_are_distinct(self):
        graph = Graph()
        graph.update([node(1, 'Video/Source', **{'media.role': 'Screen'}),
                      node(2, 'Video/Source', **{'device.api': 'libcamera'}),
                      node(3, 'Video/Source', **{'node.name': 'anonymous'})])
        state = graph.snapshot()
        self.assertTrue(state['screen'] and state['camera'] and state['video'])
        graph.update([{'id': 1}, {'id': 2}])
        self.assertFalse(graph.snapshot()['screen'] or graph.snapshot()['camera'])

    def test_obs_authentication_fixed_sha256_vector(self):
        self.assertEqual(authentication('supersecretpassword',
            'lM1GncleQOaCu9lT1yeUZhFYnqhsLLP1G5lAGo3ixaI=',
            '+IxH4CnCiqpX1rM9scsNynZzbOe4KhDeYcTNS3PDaeY='),
            '1Ct943GAT+6YQUUX47Ia/ncufilbe6+oD6lY+5kaCu4=')


if __name__ == '__main__':
    unittest.main()
