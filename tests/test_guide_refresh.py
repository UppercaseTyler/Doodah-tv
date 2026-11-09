import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, call, patch
from zoneinfo import ZoneInfo

import guide
from guide_refresh import refresh_guide_at_midnight, seconds_until_midnight


SERVER = {"host": "192.0.2.1", "port": 8090}


CHANNELS = [
    dict(name="Simple Camera", number=101, enabled=True),
    dict(name="Dayparts Camera", number=102, enabled=True,
         guide_style="dayparts", dayparts_name="the Zoo",
         dayparts_theme="standard", timezone="America/Los_Angeles"),
]


class MidnightTests(unittest.TestCase):
    def test_regular_day_and_next_midnight(self):
        zone = ZoneInfo("America/New_York")
        self.assertEqual(seconds_until_midnight(datetime(2026, 11, 4, 18, tzinfo=zone)),
                         6 * 3600)
        self.assertEqual(seconds_until_midnight(datetime(2026, 11, 4, tzinfo=zone)),
                         24 * 3600)

    def test_dst_spring_forward_day_is_23_hours(self):
        now = datetime(2026, 3, 8, tzinfo=ZoneInfo("America/New_York"))
        self.assertEqual(seconds_until_midnight(now), 23 * 3600)

    def test_dst_fall_back_day_is_25_hours(self):
        now = datetime(2026, 11, 1, tzinfo=ZoneInfo("America/New_York"))
        self.assertEqual(seconds_until_midnight(now), 25 * 3600)

    def test_schedule_is_new_york_even_when_clock_is_utc(self):
        now = datetime(2026, 11, 5, 1, tzinfo=timezone.utc)
        self.assertEqual(seconds_until_midnight(now), 4 * 3600)

    @patch("guide_refresh.seconds_until_midnight", side_effect=[10, 20, 30])
    @patch("guide_refresh.write_guide", side_effect=[OSError("disk full"), "guide.xml"])
    def test_failed_cycle_logs_and_next_cycle_retries(self, write, delay):
        stop = Mock()
        stop.is_set.return_value = False
        stop.wait.side_effect = [False, False, True]
        with self.assertLogs("guide_refresh", level="INFO") as logs:
            refresh_guide_at_midnight(CHANNELS, SERVER, stop)
        self.assertEqual(stop.wait.call_args_list, [call(10), call(20), call(30)])
        self.assertEqual(write.call_args_list, [call(CHANNELS, SERVER), call(CHANNELS, SERVER)])
        self.assertTrue(any("disk full" in line for line in logs.output))
        self.assertTrue(any("refresh complete" in line for line in logs.output))

    @patch("guide_refresh.write_guide")
    def test_stop_interrupts_wait_without_writing(self, write):
        stop = threading.Event()
        with patch("guide_refresh.seconds_until_midnight", return_value=86400):
            worker = threading.Thread(target=refresh_guide_at_midnight,
                                      args=(CHANNELS, SERVER, stop), daemon=True)
            worker.start()
            stop.set()
            worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        write.assert_not_called()


class AtomicGuideTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / "guide.xml"
        for target, value in (("guide.OUTPUT_DIR", str(self.root)),
                              ("guide.GUIDE_FILE", str(self.path))):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_replacement_preserves_existing_readers_and_publishes_full_xml(self):
        old = '<tv generator-info-name="old"/>\n'
        self.path.write_text(old)
        with self.path.open() as reader:
            guide.write_guide(CHANNELS, SERVER)
            self.assertEqual(reader.read(), old)
        root = ET.parse(self.path).getroot()
        self.assertEqual(len(root.findall("channel")), 2)
        self.assertEqual(len(root.findall("programme[@channel='101']")), 7 * 24)
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_failed_replacement_preserves_old_file_and_cleans_temporary_file(self):
        self.path.write_text("old guide")
        with patch("guide.os.replace", side_effect=OSError("disk error")):
            with self.assertRaisesRegex(OSError, "disk error"):
                guide.write_guide(CHANNELS, SERVER)
        self.assertEqual(self.path.read_text(), "old guide")
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_invalid_generated_xml_is_not_published(self):
        self.path.write_text("old guide")
        with patch("guide.generate_xmltv", return_value="<tv>"):
            with self.assertRaises(ET.ParseError):
                guide.write_guide(CHANNELS, SERVER)
        self.assertEqual(self.path.read_text(), "old guide")
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_dayparts_keep_local_timezone_and_continuous_overnight(self):
        fixed = datetime(2026, 11, 4, 17, tzinfo=timezone.utc)
        with patch("guide.datetime", wraps=datetime) as clock:
            clock.now.side_effect = lambda zone: fixed.astimezone(zone)
            guide.write_guide(CHANNELS, SERVER)
        root = ET.parse(self.path).getroot()
        overnight = root.findall("programme[@channel='102']")[0]
        self.assertEqual(overnight.get("start"), "20261103220000 -0800")
        self.assertEqual(overnight.get("stop"), "20261104070000 -0800")
        self.assertEqual(overnight.findtext("title"), "Overnight at the Zoo")

    def test_shortened_worker_cycle_updates_file_without_restart(self):
        self.path.write_text("old guide")
        old_time = self.path.stat().st_mtime_ns
        stop = threading.Event()
        complete = threading.Event()

        def write(channels, server_config):
            try:
                return guide.write_guide(channels, server_config)
            finally:
                stop.set()
                complete.set()

        with patch("guide_refresh.seconds_until_midnight", return_value=0.05), \
                patch("guide_refresh.write_guide", side_effect=write):
            worker = threading.Thread(target=refresh_guide_at_midnight,
                                      args=(CHANNELS, SERVER, stop), daemon=True)
            worker.start()
            self.assertTrue(complete.wait(2))
            worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertNotEqual(self.path.stat().st_mtime_ns, old_time)
        self.assertEqual(ET.parse(self.path).getroot().tag, "tv")


class StartupTests(unittest.TestCase):
    @patch("main.start_server")
    @patch("main.threading.Thread")
    @patch("main.write_guide", return_value="output/guide.xml")
    @patch("main.write_playlist", return_value="output/playlist.m3u")
    @patch("main.load_config")
    def test_initial_generation_precedes_worker_and_http_server(
            self, config, playlist, write, thread, server):
        import main
        config.return_value = {"channels": CHANNELS, "server": SERVER}
        order = Mock()
        order.attach_mock(write, "write")
        order.attach_mock(thread.return_value.start, "worker_start")
        order.attach_mock(server, "serve")
        main.main()
        self.assertEqual([c[0] for c in order.mock_calls],
                         ["write", "worker_start", "serve"])
        self.assertEqual(write.call_args, call(CHANNELS, SERVER))
        self.assertTrue(thread.call_args.kwargs["daemon"])
        event = thread.call_args.kwargs["args"][2]
        self.assertTrue(event.is_set())
        thread.return_value.join.assert_called_once_with(timeout=5)


if __name__ == "__main__":
    unittest.main()
