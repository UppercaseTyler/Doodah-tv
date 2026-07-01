
# Doodah TV

> Turn public livestreams into IPTV channels for Plex, Jellyfin, Emby, and other media servers.

## Overview

Doodah TV is a self-hosted application that discovers and organizes public livestreams (such as zoo cams, aquarium cams, and other webcams) and exposes them as standards-based IPTV channels.

For Doodah TV playlists, Threadfin should use:

EPG Source: XEPG

## Goals

* Support multiple stream providers (Ozolio, YouTube Live, direct HLS, and more)
* Generate standards-compliant M3U playlists
* Generate XMLTV guide data
* Be lightweight and easy to configure
* Work with existing IPTV software such as Threadfin, xTeVe, and ErsatzTV
* Keep provider-specific logic isolated from the core application

## Non-Goals (for now)

* Replace Plex, Jellyfin, or Emby
* Replace IPTV tuner software
* Record or permanently archive streams
* Implement DVR functionality
* Control PTZ (pan/tilt/zoom) cameras

## Planned Architecture

```text
Public Livestreams
        │
        ▼
    Doodah TV
        │
        ├── Resolve stream providers
        ├── Generate M3U playlist
        ├── Generate XMLTV guide
        └── Monitor stream health
        │
        ▼
Threadfin / xTeVe / ErsatzTV
        │
        ▼
Plex / Jellyfin / Emby
```

## Roadmap

### Phase 1

* [ ] Support direct HLS streams
* [ ] Generate M3U playlists
* [ ] Import channels into Plex via an IPTV bridge

### Phase 2

* [ ] Automatic Ozolio stream discovery
* [ ] YouTube Live support
* [ ] Stream health monitoring
* [ ] Automatic reconnection

### Future Ideas

* [ ] Rolling pause/rewind buffer
* [ ] Stream failover
* [ ] Rotating channels
* [ ] Web management interface
* [ ] Additional stream providers

## Why "Doodah TV"?

Scarlett, my daughter, calls giraffes "doodahs." This project started as a way to preserve one of her favorite zoo livestreams after it disappeared from YouTube, and eventually grew into the idea of turning public livestreams into a browsable television experience.

I hope it will help other families discover their favorite toddler tv channels.
