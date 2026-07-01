import os


OUTPUT_DIR = "output"
PLAYLIST_FILE = os.path.join(OUTPUT_DIR, "playlist.m3u")


def generate_m3u(streams):
    lines = ["#EXTM3U"]

    for stream in streams:
        lines.append(
            f'#EXTINF:-1 '
            f'tvg-id="{stream.number}" '
            f'tvg-name="{stream.name}" '
            f'tvg-chno="{stream.number}",'
            f'{stream.name}'
        )
        lines.append(stream.url)

    return "\n".join(lines) + "\n"


def write_playlist(streams):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    playlist = generate_m3u(streams)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as file:
        file.write(playlist)

    return PLAYLIST_FILE