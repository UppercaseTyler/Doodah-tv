import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

from guide import generate_xmltv
from logos import channel_logo_url
from playlist import generate_m3u
from server import DoodahRequestHandler


SERVER = {"host": "192.0.2.10", "port": 8090}
CHANNEL = {"name": "Zoo Camera", "number": 101}
DEFAULT_URL = (
    "https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/"
    "main/assets/logos/doodah-logo.png"
)


class ChannelLogoTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        patcher = patch("logos.LOGO_DIR", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_metadata_logo(self, channel, expected):
        root = ET.fromstring(generate_xmltv([channel], SERVER))
        icon = root.find("channel/icon")
        self.assertIsNotNone(icon)
        self.assertEqual(icon.get("src"), expected)
        self.assertIn(f'tvg-logo="{expected}"', generate_m3u([channel], SERVER))
        self.assertIsNotNone(root.find("programme"))

    def test_missing_null_and_blank_logo_share_default_in_both_formats(self):
        for channel in (CHANNEL, dict(CHANNEL, logo=None),
                        dict(CHANNEL, logo=""), dict(CHANNEL, logo="   "),
                        dict(CHANNEL, logo="doodah-logo.png")):
            with self.subTest(channel=channel):
                self.assert_metadata_logo(channel, DEFAULT_URL)

    def test_existing_local_zoo_image_used_in_both_formats(self):
        (self.root / "toledo.png").write_bytes(b"example image")
        self.assert_metadata_logo(dict(CHANNEL, logo="toledo.png"),
                                  "http://192.0.2.10:8090/logos/toledo.png")

    def test_missing_zoo_file_and_directory_fall_back(self):
        self.assert_metadata_logo(dict(CHANNEL, logo="missing.png"), DEFAULT_URL)
        (self.root / "directory.png").mkdir()
        self.assert_metadata_logo(dict(CHANNEL, logo="directory.png"), DEFAULT_URL)

    def test_external_http_and_https_urls_are_not_prefixed_or_fetched(self):
        for scheme in ("http", "https"):
            url = f"{scheme}://images.example/zoo.png?size=500&theme=light"
            self.assert_metadata_logo(dict(CHANNEL, logo=url), url)

    def test_xml_attribute_quotes_and_ampersands_are_escaped(self):
        url = 'https://images.example/zoo.png?name="Zoo"&size=500'
        root = ET.fromstring(generate_xmltv([dict(CHANNEL, logo=url)], SERVER))
        self.assertEqual(root.find("channel/icon").get("src"), url)

    def test_filename_spaces_are_encoded(self):
        (self.root / "toledo zoo.png").write_bytes(b"example image")
        self.assert_metadata_logo(dict(CHANNEL, logo="toledo zoo.png"),
                                  "http://192.0.2.10:8090/logos/toledo%20zoo.png")

    def test_unsupported_url_scheme_is_rejected(self):
        with self.assertRaises(ValueError):
            channel_logo_url(dict(CHANNEL, logo="ftp://example.com/zoo.png"), SERVER)


class LogoRouteTests(unittest.TestCase):
    def handler(self, path):
        handler = object.__new__(DoodahRequestHandler)
        handler.path = path
        handler.serve_file = Mock()
        handler.send_error = Mock()
        return handler

    @patch("server.log")
    def test_encoded_filename_is_decoded_for_local_file(self, log):
        handler = self.handler("/logos/toledo%20zoo.png")
        handler.do_GET()
        handler.serve_file.assert_called_once_with(
            Path("assets/logos/toledo zoo.png"), "image/png")

    @patch("server.log")
    def test_decoded_path_cannot_escape_logo_directory(self, log):
        for path in ("/logos/%2e%2e/config.yaml", "/logos/%2fetc/passwd"):
            handler = self.handler(path)
            handler.do_GET()
            handler.send_error.assert_called_once_with(403, "Invalid logo path")
            handler.serve_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
