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

Channels are configured in `config.yaml`.

A typical channel looks like:

```yaml
channels:
  - name: Oakland Zoo Giraffes
    number: 101
    enabled: true
    source: ozolio
    url: https://www.ozolio.com/explore/EXAMPLE
    guide_title: Oakland Zoo Giraffes
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
| `guide_title` | No | Programme title used by the current simple XMLTV guide. |
| `guide_description` | No | Programme description shown in the XMLTV guide. |
| `guide_style` | No | Options: simple, dayparts, custom |

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
| `dayparts_theme` | No | Options: `standard`, `fantasy`, `aquarium`, `random` |
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

Dispatcharr is the current recommended bridge for the Doodah development setup. Doodah itself is deliberately designed so that core provider resolution and offline behavior do not depend on a particular bridge.

## Offline fallback

When Doodah cannot resolve a configured provider, it can redirect the channel to a local HLS fallback generated from the bundled offline media.

This is the "Sleeping Giraffe" path.

The fallback belongs to Doodah rather than to the IPTV bridge. Automatic detection of provider recovery is planned but is not part of the current health behavior yet.

## Guide

Doodah currently generates a simple XMLTV guide using repeating one-hour programme blocks.

The guide system is being expanded around three styles:

- `simple` — current/default one-hour programme blocks
- `dayparts` — planned time-of-day programme titles such as Morning, Afternoon, Twilight, and Overnight
- `custom` — planned user-defined programme exceptions over an automatic baseline

Dayparts and Custom should be treated as planned features until they are implemented.

## Running with Docker

Doodah is intended to run with Docker Compose.

Before starting it:

1. Edit `config.yaml` for your network and channels.
2. Make sure the configured host address is reachable by your IPTV bridge.
3. Start the stack with Docker Compose.
4. Configure your IPTV bridge to use Doodah's playlist and XMLTV output.
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
4. Regenerate the bridge guide/XEPG.
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
