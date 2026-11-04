import io
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import m3u8

from providers.youtube import YouTubeProvider, select_hls_rendition
from server import DoodahRequestHandler


MASTER = '''#EXTM3U
#EXT-X-VERSION:6
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="low",NAME="Low",DEFAULT=YES,URI="audio/low.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="high",NAME="High",DEFAULT=YES,URI="audio/high.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=400000,CODECS="avc1.4D4015,mp4a.40.5",RESOLUTION=426x240,AUDIO="low"
video/240.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,CODECS="avc1.64001F,mp4a.40.2",RESOLUTION=1280x720,FRAME-RATE=30,AUDIO="high"
video/720.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,CODECS="vp09.00.31.08,mp4a.40.2",RESOLUTION=1920x1080,AUDIO="high"
video/vp9.m3u8
'''
URL = "https://upstream.example/live/master.m3u8?signature=example"
CHANNEL = dict(name="Camera", number=103, enabled=True, source="youtube",
               url="https://www.youtube.com/watch?v=example")


class RenditionTests(unittest.TestCase):
    def test_best_h264_keeps_matching_audio_and_absolute_signed_uris(self):
        content = MASTER.replace("video/720.m3u8", "video/720.m3u8?sig=video")
        content = content.replace("audio/high.m3u8", "audio/high.m3u8?sig=audio")
        selected = m3u8.loads(select_hls_rendition(content, URL))
        self.assertEqual(len(selected.playlists), 1)
        self.assertEqual(selected.playlists[0].stream_info.resolution, (1280, 720))
        self.assertEqual(selected.playlists[0].uri,
                         "https://upstream.example/live/video/720.m3u8?sig=video")
        self.assertEqual(len(selected.media), 1)
        self.assertEqual(selected.media[0].group_id, "high")
        self.assertEqual(selected.media[0].uri,
                         "https://upstream.example/live/audio/high.m3u8?sig=audio")

    def test_quality_uses_resolution_before_bandwidth(self):
        content = MASTER.replace("BANDWIDTH=400000", "BANDWIDTH=9000000")
        selected = m3u8.loads(select_hls_rendition(content, URL))
        self.assertEqual(selected.playlists[0].stream_info.resolution, (1280, 720))

    def test_muxed_rendition_needs_no_external_audio(self):
        content = '''#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=2500000,CODECS="avc1.64001F,mp4a.40.2",RESOLUTION=1280x720
video.m3u8
'''
        selected = m3u8.loads(select_hls_rendition(content, URL))
        self.assertEqual(len(selected.playlists), 1)
        self.assertFalse(selected.media)

    def test_single_media_playlist_still_redirects(self):
        content = "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nsegment.ts\n"
        self.assertIsNone(select_hls_rendition(content, URL))

    def test_missing_audio_group_fails_instead_of_dropping_audio(self):
        content = "\n".join(line for line in MASTER.splitlines()
                            if not line.startswith("#EXT-X-MEDIA:"))
        with self.assertRaisesRegex(ValueError, "missing audio group"):
            select_hls_rendition(content, URL)

    def test_unsupported_or_invalid_manifest_fails(self):
        for content in ("<html>error</html>", "#EXTM3U\n",
                        MASTER.replace("avc1.", "hvc1.")):
            with self.subTest(content=content[:30]):
                with self.assertRaises(ValueError):
                    select_hls_rendition(content, URL)


class ProviderAndServerTests(unittest.TestCase):
    @patch("providers.youtube.requests.get")
    @patch("providers.youtube.subprocess.run")
    def test_demuxed_selector_fallback_keeps_audio(self, run, get):
        run.side_effect = [Mock(stdout="NA\n"), Mock(stdout=URL + "\n")]
        get.return_value = Mock(text=MASTER, url=URL)
        stream = YouTubeProvider().resolve(CHANNEL)
        self.assertEqual(len(m3u8.loads(stream.hls_manifest).media), 1)
        self.assertEqual(run.call_args_list[1].args[0][4],
                         "bestvideo[protocol^=m3u8]")

    @patch("providers.youtube.subprocess.run")
    def test_private_video_preserves_diagnostics(self, run):
        import subprocess
        run.side_effect = subprocess.CalledProcessError(
            1, ["yt-dlp"], stderr="Private video")
        with self.assertRaisesRegex(RuntimeError, "Private video"):
            YouTubeProvider().resolve(CHANNEL)

    def handler(self):
        handler = object.__new__(DoodahRequestHandler)
        handler.wfile = io.BytesIO()
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        return handler

    @patch("server.log")
    @patch("server.load_config")
    @patch.dict("server.PROVIDERS")
    def test_master_response_and_existing_redirect(self, config, log):
        from providers.base import ResolvedStream
        import server
        config.return_value = {"channels": [CHANNEL]}
        provider = Mock()
        server.PROVIDERS["youtube"] = provider
        for manifest, status in (("#EXTM3U\n", 200), (None, 302)):
            provider.resolve.return_value = ResolvedStream(
                **{k: CHANNEL[k] for k in ("name", "number", "enabled", "source")},
                url=URL, guide_title="Camera", guide_description="Camera",
                hls_manifest=manifest)
            handler = self.handler()
            handler.serve_channel("/channel/103")
            handler.send_response.assert_called_once_with(status)
            if manifest:
                self.assertEqual(handler.wfile.getvalue(), manifest.encode())
                handler.send_header.assert_any_call("Cache-Control", "no-store")
            else:
                handler.send_header.assert_any_call("Location", URL)

    @patch("server.log")
    @patch("server.load_config")
    @patch("server.OFFLINE_MANAGER")
    @patch.dict("server.PROVIDERS")
    def test_resolution_failure_still_redirects_to_sleeping_giraffe(self, offline, config, log):
        import server
        config.return_value = {"channels": [CHANNEL],
                               "server": {"host": "192.0.2.1", "port": 8090}}
        server.PROVIDERS["youtube"] = Mock()
        server.PROVIDERS["youtube"].resolve.side_effect = RuntimeError("Private video")
        offline.get_or_start.return_value = Path("output/offline/103/playlist.m3u8")
        handler = self.handler()
        handler.serve_channel("/channel/103")
        handler.send_response.assert_called_once_with(302)
        handler.send_header.assert_any_call(
            "Location", "http://192.0.2.1:8090/offline/103/playlist.m3u8")


if __name__ == "__main__":
    unittest.main()
