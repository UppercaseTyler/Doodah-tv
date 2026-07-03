
# Doodah TV

> Turn public livestreams into IPTV channels for Plex, Jellyfin, Emby, and other media servers.

## Overview

Doodah TV is a lightweight IPTV backend that turns live internet streams into television channels. It aggregates streams from multiple providers, resolves dynamic URLs (such as YouTube live streams), generates M3U playlists and XMLTV guides, and exposes stable channel endpoints for Plex, Jellyfin, Threadfin, and other IPTV clients.

For Doodah TV playlists, Threadfin should use:

EPG Source: XEPG

## Features

- Live IPTV channel generation
- XMLTV guide generation
- Stable HTTP channel endpoints
- Provider architecture for multiple stream types
- Static HLS support
- YouTube Live support via yt-dlp
- Automatic YouTube URL resolution
- Docker deployment
- Plex and Threadfin compatible

## Added a channel but it doesn't appear in Plex?

Update Playlist
Update XMLTV
Verify the channel is assigned to the correct XMLTV source in Threadfin
Regenerate XEPG
Refresh the Plex guide

## Goals

* Support multiple stream providers (Ozolio, YouTube Live, direct HLS, and more)
* Generate standards-compliant M3U playlists
* Generate XMLTV guide data
* Be lightweight and easy to configure
* Work with existing IPTV software such as Threadfin
* Keep provider-specific logic isolated from the core application

## Non-Goals (for now)

* Replace Plex, Jellyfin, or Emby
* Replace IPTV tuner software
* Record or permanently archive streams
* Control PTZ (pan/tilt/zoom) cameras


## Roadmap

### Phase 1

* [x] Support direct HLS streams
* [x] Generate M3U playlists
* [x] Import channels into Plex via an IPTV bridge

### Phase 2

* [ ] Automatic Ozolio stream discovery
* [x] YouTube Live support
* [x] Stream health monitoring
* [x] Automatic reconnection

### Future Ideas

* [x] Rolling pause/rewind buffer
* [ ] Stream failover
* [ ] Rotating channels
* [ ] Web management interface
* [ ] Additional stream providers

## Why "Doodah TV"?

Scarlett, my daughter, calls giraffes "doodahs." This project started as a way to preserve one of her favorite zoo livestreams after it disappeared from YouTube, and eventually grew into the idea of turning public livestreams into a browsable television experience.

I hope it will help other families discover their favorite toddler tv channels.
