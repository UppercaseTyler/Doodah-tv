import os


OUTPUT_DIR = "output"
PLAYLIST_FILE = os.path.join(OUTPUT_DIR, "playlist.m3u")

def generate_m3u(streams, server_config):
    lines = ["#EXTM3U"]

    host = server_config["host"]
    port = server_config["port"]

    for stream in streams:
        channel_url = f"http://{host}:{port}/channel/{stream.number}"

        lines.append(
            f'#EXTINF:-1 '
            f'tvg-id="{stream.number}" '
            f'tvg-name="{stream.name}" '
            f'tvg-chno="{stream.number}",'
            f'{stream.name}'
        )
        lines.append(channel_url)

    return "\n".join(lines) + "\n"

def write_playlist(streams, server_config):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    playlist = generate_m3u(streams, server_config)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as file:
        file.write(playlist)

    return PLAYLIST_FILE