# Doodah-TV 🦒

Doodah-TV is a lightweight Python application that turns live internet streams into IPTV channels for use with Plex and other IPTV clients.

It was originally built for a very important use case: putting live zoo cameras on the television for my daughter.

Doodah resolves provider-specific stream URLs, generates an M3U playlist and XMLTV guide, and provides a stable channel URL that an IPTV bridge can use. When a provider is unavailable, Doodah can serve a local offline fallback instead.

Doodah is intentionally **not** a media server and does not play a local media library.

## How it works

```text
Plex / IPTV client
        ↓
IPTV bridge (Dispatcharr, Threadfin, etc)
        ↓
Doodah-TV /channel/<number>
        ↓
provider resolution
   ↙             ↘
live             unavailable
 ↓                   ↓
upstream URL      offline HLS
```

For live streams, Doodah resolves the current provider URL and redirects the IPTV bridge to it. Live media then flows from the provider through the bridge; Doodah does not permanently proxy the video.

For YouTube master playlists, Doodah returns a small HLS master playlist with
the highest-resolution H.264 rendition and its matching AAC audio group.
This handles both muxed and separate audio/video layouts without exposing all
alternate qualities to the bridge. The bridge fetches the selected playlists
and media directly from YouTube. If no compatible rendition is available,
resolution fails and the normal offline fallback is used.

## Features

- M3U playlist generation
- XMLTV guide generation
- Stable `/channel/<number>` URLs
- Provider-specific stream resolution
- HLS streams
- YouTube livestreams
- Ozolio cameras
- Per-channel enable/disable configuration
- Local offline fallback ("Sleeping Giraffe")
- Docker deployment
- Designed to remain lightweight and bridge-agnostic

## Channel configuration

Channels are configured in a local `config.yaml`. Create it from the committed example:

```bash
cp config.example.yaml config.yaml
```

Edit the server address and replace the placeholder cameras before enabling them.
The live config and deployment backups are ignored by Git and excluded from Docker builds.
Keep a separate backup of your config; Git does not preserve it.

A typical channel looks like:

```yaml
channels:
  - name: Oakland Zoo Giraffes
    number: 101
    enabled: true
    source: ozolio
    url: https://www.ozolio.com/explore/EXAMPLE
    guide_style: simple
    guide_description: Live giraffe habitat from the Oakland Zoo.
```

Channel fields are intentionally ordered from user-facing identity to implementation details.

### Core channel fields

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Human-readable channel name. |
| `number` | Yes | IPTV channel number. Must be unique. |
| `enabled` | Yes | Whether the channel is included in generated output. |
| `source` | Yes | Provider used to resolve the stream. |
| `url` | Yes | Provider page or stream URL. |
| `guide_description` | No | Programme description shown in the XMLTV guide. |
| `guide_style` | No | Options: `simple` (default), `dayparts` |

### Supported providers

Current providers:

- HLS
- YouTube
- Ozolio

Planned providers:

- EarthCam

### Guide style specific fields

| Field | Required | Description |
| --- | --- | --- |
| `dayparts_name` | No | Friendly location name used in Dayparts titles, such as `Morning at Oakland Zoo`. |
| `dayparts_theme` | No | Options: `standard` (default), `fantasy`, `poetic`, `aquarium`, `bananas`, `random` |
| `timezone` | No | IANA timezone (for example `America/Denver`) used to match Dayparts to the camera's local time. |

## Server configuration

```yaml
server:
  bind: 0.0.0.0
  host: 192.168.1.100
  port: 8090
```

`host` should be an address that your IPTV bridge can use to reach Doodah.

Doodah exposes resources including:

```text
/playlist.m3u
/guide.xml
/channel/<number>
/offline/<channel>/<file>
```

## IPTV bridge

Doodah is designed to sit behind an IPTV bridge that presents its channels to Plex or another TV client.

Dispatcharr is the bridge used in Doodah's development setup and the recommended starting point. Doodah is bridge-agnostic and should work with any compatible IPTV bridge; its provider resolution and offline behavior do not depend on Dispatcharr.
Plex can fetch XMLTV directly from Doodah at `http://<host>:8090/guide.xml`, independently of the bridge used for channel delivery.

## Offline fallback

When Doodah cannot resolve a configured provider, it can redirect the channel to a local HLS fallback generated from the bundled offline media.

This is the "Sleeping Giraffe" path.

The fallback belongs to Doodah rather than to the IPTV bridge. Automatic detection of provider recovery is planned but is not part of the current health behavior yet.

## Guide

Doodah generates seven days of XMLTV with two supported styles:

- `simple` — default repeating one-hour blocks titled with the channel name.
- `dayparts` — time-of-day titles using the channel's timezone and selected theme.

Overnight remains one continuous programme from 22:00 to 07:00 across midnight.
The `random` theme deterministically chooses `standard`, `fantasy`, or `poetic`
for each date/channel/daypart; `aquarium` and `bananas` are explicit-only.
See `config.example.yaml` for all Dayparts options and defaults.

The playlist and guide are generated at startup. The guide is then regenerated
daily at midnight in `America/New_York`, independently of channel timezones.
Each refresh uses the startup channel configuration. After a config edit,
restart Doodah to regenerate both the playlist and guide with the new settings.

Guide refreshes publish a complete, validated XMLTV file using an atomic
replacement. If a scheduled refresh fails, Doodah logs the error, retains the
previous guide, and retries the next midnight. Plex and other guide consumers
fetch the file on their own schedules; generation does not trigger an import.

## Running with Docker

Doodah is intended to run with Docker Compose.

Before starting it:

1. Copy `config.example.yaml` to `config.yaml`, then edit it for your network and channels.
2. Make sure the configured host address is reachable by your IPTV bridge.
3. Start Doodah with `docker compose up -d --build doodah-tv`. The supplied Compose file also includes an optional, unmodified Dispatcharr service; it is not required to run Doodah.
4. Configure your IPTV bridge to use Doodah's playlist. Configure Plex or your guide consumer to fetch Doodah's XMLTV directly if desired.
5. Add the bridge as a tuner in Plex or your IPTV client.

## Project status

Doodah-TV is under active development.

The core provider-resolution, playlist, guide, and offline-fallback architecture is working. Guide improvements and automatic recovery from offline fallback are active roadmap items.

See `architecture.md` for the design principles and internal component responsibilities.

## Troubleshooting

### Channel doesn't appear in Plex

1. Update the playlist in your IPTV bridge.
2. Update the XMLTV source.
3. Verify the channel is assigned to the correct XMLTV source.
4. If your bridge manages the guide, regenerate its guide/XEPG.
5. Refresh the Plex guide.

### Resolving the wrong video (or no video) from Ozolio

If an Ozolio page contains multiple embedded cameras, add the camera's object ID to your channel configuration:

```yaml
object: CAMERA_OBJECT_ID
```

The object ID can usually be found using your browser's developer tools.

If that still doesn't work, the stream may use an Ozolio implementation that Doodah does not support yet.

## Why "Doodah-TV"?

Scarlett, my daughter, calls giraffes "doodahs." This project started as a way to preserve one of her favorite zoo livestreams after it disappeared from YouTube, and eventually grew into the idea of turning public livestreams into a browsable television experience.

I hope it will help other families discover their favorite toddler tv channels.

## License

Copyright (c) 2026 Tyler Kimbley.

Doodah-TV is licensed under the GNU General Public License, version 3 only
(SPDX: `GPL-3.0-only`). This includes the project-created logo and offline
fallback artwork and video bundled in this repository.

You may use, modify, and redistribute Doodah-TV under the GPLv3, including
commercially. Distribution of covered modified versions must comply with the
GPLv3's source-code and licensing requirements. The software comes without
warranty. See [LICENSE](LICENSE) for the full terms.

External services, livestream content, and separately installed software such
as Dispatcharr retain their respective licenses and terms; Doodah's license
does not grant rights to that content or software.
