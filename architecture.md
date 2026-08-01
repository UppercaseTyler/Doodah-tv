# Doodah-TV Architecture

## Purpose

Doodah-TV is a lightweight resolver and control layer for turning live internet streams into IPTV channels.

Its job is to:

- describe channels in one configuration file
- resolve provider-specific live stream URLs
- generate M3U and XMLTV output
- provide stable `/channel/<number>` endpoints
- choose between a live provider and Doodah's local offline fallback

Doodah is **not** intended to become a permanent live-media proxy.

## Core design principles

### Keep Doodah lightweight

Doodah should perform control-plane work: configuration, provider resolution, guide generation, and fallback decisions. Whenever possible, live video should flow directly from the upstream provider through the IPTV bridge rather than through Doodah.

### Keep provider quirks inside providers

The server should not need to understand how YouTube, Ozolio, or another source discovers its playable stream. Provider-specific logic belongs in the provider layer.

### Keep the IPTV bridge replaceable

Doodah may be used with Dispatcharr, Threadfin, another IPTV bridge, or a compatible direct client. Core Doodah behavior should not require bridge-specific failover configuration.

### Prefer simple, explicit architecture

Doodah favors small components with clear responsibilities over generic frameworks or abstractions added for hypothetical future needs.

## System overview

```text
Plex / IPTV client
        ↓
IPTV bridge
        ↓
GET /channel/<number>
        ↓
Doodah-TV
        ↓
configured provider
        ↓
resolve current playable URL
        ↓
HTTP redirect
        ↓
IPTV bridge connects to live upstream
```

The redirect is an important architectural boundary. Once Doodah has resolved the provider, it hands the playable URL to the bridge. Doodah does not continuously receive and retransmit the live media.

## Channel request flow

A channel number is a stable Doodah-facing identity even when the provider's underlying stream URL is temporary.

```text
/channel/102
    ↓
load channel 102
    ↓
source: youtube
    ↓
YouTube provider
    ↓
resolve current HLS URL
    ↓
302 redirect
```

The IPTV bridge can continue to know the channel as `/channel/102`; Doodah handles rediscovery of the current provider URL whenever that endpoint is requested.

## Provider layer

Each channel declares a `source`, such as `hls`, `youtube`, or `ozolio`.

```text
channel configuration
        ↓
provider registry
        ↓
matching provider
        ↓
provider.resolve(channel)
        ↓
playable stream URL
```

This boundary prevents provider-specific session initialization, page parsing, URL extraction, and other quirks from leaking into the HTTP server.

## Offline fallback

Doodah owns its offline fallback behavior.

If provider resolution fails, Doodah can return a local HLS stream generated from offline media rather than requiring the IPTV bridge to know about a separate fallback channel.

```text
GET /channel/102
        ↓
provider resolution fails
        ↓
offline manager
        ↓
local HLS for channel 102
        ↓
redirect to /offline/102/playlist.m3u8
```

The offline media path is the intentional exception to the rule that Doodah does not handle media: Doodah owns this media because it generates the fallback locally.

### `offline_manager.py`

The offline manager owns the lifecycle of local fallback media. It should not become responsible for provider health, XMLTV generation, IPTV bridge behavior, or general live-stream proxying.

## IPTV bridge responsibility

The IPTV bridge handles transport between Doodah's channel endpoints and the final TV client. Dispatcharr is the recommended bridge in the current development deployment.

The bridge is responsible for maintaining playback, buffering/transcoding when required, detecting transport failure, and reconnecting the configured channel URL.

Doodah remains responsible for provider resolution, choosing live versus fallback media, and generating its playlist and guide.

## Dispatcharr reconnect patch

Doodah currently depends on reliable reconnection to the original configured `/channel/<number>` URL after an upstream stream failure.

A reconnect issue was identified in Dispatcharr where the health monitor could set `needs_reconnect`, while `_process_stream_data()` did not include that flag in its loop-exit conditions. This could prevent control from returning to Dispatcharr's existing reconnect path.

Doodah's deployment currently carries the corresponding small patch against a pinned Dispatcharr image while the upstream contribution is under review.

This is a deployment compatibility patch, not Doodah business logic.

## Guide architecture

Guide generation is separate from live playback.

```text
config.yaml
    ↓
guide.py
    ↓
XMLTV
    ↓
IPTV bridge / TV client
```

Changing guide metadata does not change the video stream.

### Simple

`simple` is the current/default guide behavior and generates repeating one-hour programme blocks.

### Dayparts — planned

Dayparts will generate larger programme blocks based on the local time of the camera:

```text
07:00–11:00  Morning
11:00–15:00  Midday
15:00–18:00  Afternoon
18:00–20:00  Evening
20:00–22:00  Twilight
22:00–07:00  Overnight
```

Dayparts are intended to use a per-channel timezone, falling back to the global default timezone.

A separate `dayparts_name` will allow natural guide titles such as `Morning at Oakland Zoo` without requiring the IPTV channel name itself to use that wording.

Dayparts should be implemented as a separate guide generator rather than adding time-of-day conditionals throughout Simple.

### Custom — planned

Custom guide behavior is intended to provide an automatic baseline with explicitly configured programme exceptions. It should remain separate from Dayparts rather than turning Dayparts into a generic scheduling framework.

## Planned health engine

The health engine is planned recovery behavior, not current functionality.

Its purpose is to answer: how does Doodah know the provider has come back?

```text
provider unavailable
        ↓
serve offline fallback
        ↓
background provider-aware health checks
        ↓
provider appears healthy
        ↓
require consecutive successful checks
        ↓
stop that channel's fallback FFmpeg
        ↓
bridge sees fallback stream end
        ↓
bridge reconnects /channel/<number>
        ↓
Doodah resolves live provider again
```

The first implementation is intended to use lightweight in-memory state, one recovery worker per offline channel, and a backoff polling cadence. Provider-specific health checks should remain in the provider layer.

The health engine should not introduce a permanent live-media proxy.

## Configuration

Channel configuration should remain readable without requiring a UI.

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

The README is the primary user-facing configuration reference. This document records the architectural decisions behind that configuration.

## Architecture decisions

### Configuration field order

**Decision**

Core channel configuration fields shall appear in the following order:

```text
name
number
enabled
source
url
```

Additional feature-specific fields follow the core channel identity and source fields.

**Rationale**

The fields are ordered from user-facing identity to implementation details. This improves readability and keeps configuration files consistent across installations.

Field names should favor explicit meaning over brevity. Configuration should remain understandable to someone inspecting or debugging the repository directly, even if a future UI hides those implementation details.

## Non-goals

Doodah is not intended to become:

- a replacement for Plex
- a local-media playout server
- a permanent proxy for all live video
- a Dispatcharr-specific extension
- a generic monitoring platform
- a generic scheduling framework

Features should be added only when they support Doodah's core job of turning live internet streams into simple, reliable IPTV channels.
