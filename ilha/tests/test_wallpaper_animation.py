import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wallpaper_store as wallpaper
import theme_store as themes
import theme_sync
import launcher_actions


class AnimatedWallpaperTests(unittest.TestCase):
    def test_validation_rejects_urls_traversal_symlinks_and_non_video(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);walls=root/'Wallpapers';walls.mkdir()
            outside=root/'outside.mp4';outside.write_bytes(b'x')
            (walls/'link.mp4').symlink_to(outside)
            with patch.object(wallpaper,'root',return_value=walls), patch.object(wallpaper.subprocess,'run') as run:
                for path in ['https://example.com/video.mp4',str(outside),str(walls/'link.mp4'),str(walls/'missing.mp4')]:
                    with self.assertRaises(ValueError):wallpaper.describe(path)
                run.assert_not_called()

    def test_valid_metadata_and_codec_probe_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'video # teste.mp4';path.write_bytes(b'x')
            result=Mock(returncode=0,stdout=json.dumps({'streams':[{'width':320,'height':180}]}))
            with patch.object(wallpaper,'root',return_value=root), patch.object(wallpaper,'multimedia_available',return_value=True), patch.object(wallpaper.shutil,'which',return_value='/usr/bin/ffprobe'), patch.object(wallpaper.subprocess,'run',return_value=result) as run:
                self.assertEqual(wallpaper.describe(str(path))['kind'],'video')
                self.assertEqual(run.call_args.args[0][-1],str(path))
                self.assertIn('-protocol_whitelist',run.call_args.args[0])
                result.stdout='{"streams":[]}'
                with self.assertRaisesRegex(ValueError,'não contém'):wallpaper.describe(str(path))

    def test_selection_preserves_preferences_and_invalid_update_is_atomic(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'config.json'
            config.write_text(json.dumps({'theme':'nord','wallpaper':{'pauseOnBattery':False}}))
            with patch.object(themes,'CONFIG',config), patch.object(themes,'USER_THEMES',root/'themes'), patch.object(wallpaper,'describe',return_value={'path':'/wall/video.mp4'}), patch.object(wallpaper,'thumbnail'):
                response=themes.perform('animated_wallpaper',{'path':'/wall/video.mp4'})
                self.assertEqual(response['config']['theme'],'nord')
                self.assertFalse(response['config']['wallpaper']['pauseOnBattery'])
                self.assertTrue(response['config']['wallpaper']['enabled'])
                previous=config.read_text()
                with self.assertRaises(ValueError):themes.perform('preferences',{'values':{'wallpaper':{'paused':'yes'}}})
                self.assertEqual(config.read_text(),previous)

    def test_missing_multimedia_reports_dependency_instead_of_loading_broken_ui(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'file.gif';path.write_bytes(b'x')
            with patch.object(wallpaper,'root',return_value=root), patch.object(wallpaper.shutil,'which',return_value='ffprobe'), patch.object(wallpaper.subprocess,'run',return_value=Mock(returncode=0,stdout='{"streams":[{"width":10,"height":10}]}')), patch.object(wallpaper,'multimedia_available',return_value=False):
                with self.assertRaisesRegex(ValueError,'qt6-multimedia'):wallpaper.describe(str(path))

    def test_theme_sync_reactivates_associated_video_after_manual_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);video=root/'video.mp4';video.write_bytes(b'x')
            state=root/'ilha/wallpaper.json';state.parent.mkdir();state.write_text(json.dumps({'path':str(video)}))
            theme=json.loads((Path(__file__).resolve().parents[1]/'themes/nord.json').read_text())
            config={'sync':{'wallpaper':True},'wallpapers':{'nord':str(video)},'wallpaper':{'enabled':False,'path':str(video)}}
            with patch.dict('os.environ',{'XDG_STATE_HOME':str(root)}),patch.object(launcher_actions,'apply_wallpaper') as apply:
                result=theme_sync.synchronize({'theme':theme,'config':config})
                self.assertTrue(result['ok']);apply.assert_called_once_with(str(video))
                apply.reset_mock();config['wallpaper']['enabled']=True
                theme_sync.synchronize({'theme':theme,'config':config});apply.assert_not_called()


if __name__=='__main__':unittest.main()
