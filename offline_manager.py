from dataclasses import dataclass
from pathlib import Path
import subprocess
import threading
import time


@dataclass
class OfflineWorker:
    channel_number: int
    process: subprocess.Popen
    playlist_path: Path
    log_file: object


class OfflineManager:
    def __init__(
        self,
        source_path: Path = Path("assets/offline/offline.mp4"),
        output_root: Path = Path("output/offline"),
    ) -> None:
        self.source_path = source_path
        self.output_root = output_root
        self._workers: dict[int, OfflineWorker] = {}
        self._lock = threading.Lock()
       
    def get_or_start(self, channel_number: int) -> Path:
        with self._lock:
            worker = self._workers.get(channel_number)

            if worker and worker.process.poll() is None:
                return worker.playlist_path

            return self._start_worker(channel_number)
    
    def _start_worker(self, channel_number: int) -> Path:
        channel_dir = self.output_root / str(channel_number)
        channel_dir.mkdir(parents=True, exist_ok=True)

        playlist_path = channel_dir / "playlist.m3u8"
        segment_pattern = channel_dir / "segment_%03d.ts"
        log_path = channel_dir / "ffmpeg.log"
        log_file = open(log_path, "ab")
        playlist_path.unlink(missing_ok=True)

        for segment_path in channel_dir.glob("segment_*.ts"):
            segment_path.unlink()

        cmd = self._build_ffmpeg_command(
            segment_pattern,
            playlist_path,
        )

        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        
        worker = OfflineWorker(
            channel_number=channel_number,
            process=process,
            playlist_path=playlist_path,
            log_file=log_file,
        )

        self._workers[channel_number] = worker

        for _ in range(150):
            if playlist_path.exists() and playlist_path.stat().st_size > 0:
                return playlist_path

            if process.poll() is not None:
                self._workers.pop(channel_number, None)
                log_file.close()
                raise RuntimeError(
                    f"Offline FFmpeg exited before creating a playlist "
                    f"for channel {channel_number}"
                )

            time.sleep(0.1)

        process.terminate()
        self._workers.pop(channel_number, None)
        log_file.close()

        raise TimeoutError(
            f"Timed out waiting for offline playlist "
            f"for channel {channel_number}"
        )
    
    def _build_ffmpeg_command(
        self,
        segment_pattern: Path,
        playlist_path: Path,
    ) -> list[str]:
        return [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-re",
            "-stream_loop",
            "-1",
            "-i",
            str(self.source_path),
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-f",
            "hls",
            "-hls_time",
            "2",
            "-hls_list_size",
            "6",
            "-hls_flags",
            "delete_segments+omit_endlist+independent_segments",
            "-hls_segment_filename",
            str(segment_pattern),
            str(playlist_path),
        ]
    
    def stop(self, channel_number: int) -> None:
        with self._lock:
            worker = self._workers.pop(channel_number, None)

        if worker is None:
            return

        if worker.process.poll() is None:
            worker.process.terminate()

            try:
                worker.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.process.kill()
                worker.process.wait()

        worker.log_file.close()

    def stop_all(self) -> None:
        with self._lock:
            channel_numbers = list(self._workers.keys())

        for channel_number in channel_numbers:
            self.stop(channel_number)

