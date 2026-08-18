# QManager for Home Assistant

Custom Home Assistant integration for [QManager](https://github.com/dr-dolomite/QManager), the web UI that runs
directly on Quectel RM520N/RM551E/RM500Q-class cellular modems. Polls the modem's status endpoint over the network
(e.g. via Tailscale) and exposes signal, connectivity, and device health as entities, plus a couple of safe controls.

## What you get

**Sensors:** network type (5G-NSA/LTE/...), carrier, service status, WAN IPv4, LTE band/RSRP/RSRQ/SINR,
5G NR band/RSRP/RSRQ/SINR, modem temperature, CPU usage, memory used, uptime, connection uptime, ping latency,
packet loss, watchdog state, watchdog recovery count.

**Binary sensors:** internet available, modem reachable, carrier aggregation active, SIM failover active, watchdog
enabled.

**Button:** Start cell scan.

**Services:**
- `qmanager.send_at_command` — send a raw AT command to the modem, returns the response text.
- `qmanager.start_cell_scan` — same as the button, callable from automations/scripts.

This is intentionally read-heavy. It does not expose band locking, reboot, APN, or SMS — those are higher-blast-radius
actions best done from the QManager web UI directly, at least for v1.

## Requirements

- Home Assistant 2024.6+ (uses the `ConfigEntry.runtime_data` pattern).
- Network reachability from Home Assistant to the modem's QManager web UI (LAN, VPN, or Tailscale).
- The QManager password you set during first-time setup.

## Installation

### Option A — manual copy

Copy `custom_components/qmanager/` into your Home Assistant config directory, so you end up with:

```
<config>/custom_components/qmanager/__init__.py
<config>/custom_components/qmanager/manifest.json
...
```

Then restart Home Assistant.

### Option B — HACS custom repository

If you push this repo to GitHub, add it in HACS as a custom repository (type: Integration), install it, and restart
Home Assistant.

## Setup

Settings → Devices & Services → Add Integration → "QManager Cell Modem". You'll need:

- **Host** — the modem's IP address (e.g. its Tailscale IP)
- **Port** — usually `80`
- **Password** — your QManager login password
- **Use HTTPS** — leave off unless you've put TLS in front of it

The config flow logs in and pulls a status snapshot to validate the connection before creating the entry, and uses
the modem's IMEI as the unique ID so re-adding the same modem won't create duplicates.

The poll interval defaults to 30 seconds and can be changed from the integration's **Configure** options.

## Notes on the QManager API

- Auth is a cookie session (`qm_session`) obtained via `POST /cgi-bin/quecmanager/auth/login.sh`. The client
  re-logs-in automatically on a 401.
- Status comes from `GET /cgi-bin/quecmanager/at_cmd/fetch_data.sh`, which is a cache written by QManager's own
  poller (updated every 2-30s depending on QManager's own config) — this integration's poll interval controls how
  often *we* read that cache, not how often the modem itself is queried.
- Live bandwidth (rx/tx throughput) is served by a separate opt-in WebSocket on port 8838 in QManager and is not
  currently pulled in here.
