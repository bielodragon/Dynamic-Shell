import sys
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import launcher_backend as launcher
import launcher_actions as actions


class LauncherTests(unittest.TestCase):
    def test_calculator_arithmetic_functions_and_constants(self):
        self.assertEqual(launcher.calculate('sqrt(144) + 2**3'), '20')
        self.assertEqual(launcher.calculate('2 + 3 * 4'), '14')
        self.assertEqual(launcher.calculate('round(pi, 2)'), '3.14')
        self.assertEqual(launcher.calculate('sin(0)'), '0')

    def test_calculator_rejects_code_and_expensive_expressions(self):
        for value in ('__import__("os").system("true")', '(1).__class__', '[1,2]',
                      '2**100000', '1/0', 'sqrt(-1)', 'True', '1e200'):
            with self.assertRaises(Exception): launcher.calculate(value)

    def test_terminal_only_constructs_explicit_terminal_action(self):
        with patch.object(launcher.shutil, 'which', return_value='/usr/bin/xdg-terminal-exec'), patch.object(launcher.subprocess, 'Popen') as start:
            launcher.terminal('printf "%s" "$(literal)"')
            self.assertEqual(start.call_args.args[0], ['/usr/bin/xdg-terminal-exec','sh','-lc','printf "%s" "$(literal)"'])
            self.assertNotIn('shell', start.call_args.kwargs)

    def test_history_id_is_numeric_and_never_a_command(self):
        with patch.object(launcher.subprocess, 'run') as execute:
            with self.assertRaises(ValueError): launcher.perform('copy-history', {'id':'1; touch /tmp/test'})
            execute.assert_not_called()

    def test_copy_limits_size_before_touching_clipboard(self):
        with patch.object(launcher.subprocess, 'run') as execute:
            with self.assertRaises(ValueError): launcher.copy(b'x' * (8 * 1024 * 1024 + 1))
            execute.assert_not_called()

    def test_wallpaper_directory_filters_files_and_escaping_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); walls = root / 'Wallpapers'; walls.mkdir()
            (walls / 'foto com espaços.png').write_bytes(b'image')
            (walls / 'comando.sh').write_text('exit 1')
            (root / 'fora.png').write_bytes(b'image')
            (walls / 'atalho.png').symlink_to(root / 'fora.png')
            with patch.object(actions, 'wallpaper_directory', return_value=walls):
                rows = actions.wallpapers()
                self.assertEqual([row['title'] for row in rows], ['foto com espaços'])
                self.assertIn('foto%20com%20espa', rows[0]['thumbnail'])
                with patch.object(actions.subprocess, 'run') as run:
                    with self.assertRaises(ValueError): actions.apply_wallpaper(str(root / 'fora.png'))
                    run.assert_not_called()

    def test_wallpaper_and_lock_pass_arguments_without_a_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            walls = Path(temporary); image = walls / 'a $(literal).png'; image.write_bytes(b'image')
            with patch.object(actions, 'wallpaper_directory', return_value=walls), patch.object(actions.shutil, 'which', return_value='/usr/bin/caelestia'), patch.object(actions.subprocess, 'run') as run:
                run.return_value.returncode = 0
                actions.apply_wallpaper(str(image))
                self.assertEqual(run.call_args.args[0], ['/usr/bin/caelestia','wallpaper','-f',str(image),'-N'])
                self.assertNotIn('shell', run.call_args.kwargs)
                actions.lock()
                self.assertEqual(run.call_args.args[0], ['/usr/bin/caelestia','shell','lock','lock'])

    def test_random_wallpaper_reports_empty_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(actions, 'wallpaper_directory', return_value=Path(temporary)), patch.object(actions, 'apply_wallpaper') as apply:
                with self.assertRaisesRegex(ValueError, 'Pictures/Wallpapers'): actions.random_wallpaper()
                apply.assert_not_called()


if __name__ == '__main__': unittest.main()
