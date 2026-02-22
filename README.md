<div align="center">

# ВАРТА /// VARTA

### Real-Time Tactical Surveillance for Ukraine

**6 data sources. Zero API keys. One HTML file.**

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg?style=flat-square)](LICENSE)
[![Single File](https://img.shields.io/badge/Architecture-Single_HTML_File-00ff88.svg?style=flat-square)](#tech-stack)
[![No API Keys](https://img.shields.io/badge/API_Keys-None_Required-ff2952.svg?style=flat-square)](#quick-start)
[![Data Sources](https://img.shields.io/badge/Data_Sources-6_Independent-ffb020.svg?style=flat-square)](#data-sources)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-00e5ff.svg?style=flat-square)](https://github.com/clmrie/varta/pulls)

<br>

<img src="assets/screenshot.png" alt="VARTA Dashboard" width="900">

*A military command center in your browser — monitoring Ukraine's airspace, frontlines, and threat landscape in real time.*

<br>

[**Live Demo**](https://clmrie.github.io/varta) · [Report Bug](https://github.com/clmrie/varta/issues) · [Request Feature](https://github.com/clmrie/varta/issues)

</div>

---

## What is VARTA?

**VARTA** (*Варта* — Ukrainian for "The Guard") is a real-time tactical intelligence dashboard that monitors the war in Ukraine using **6 independent public data sources**.

It correlates air raid alerts, satellite fire detection, seismic sensors, frontline positions, news feeds, and air quality data — all rendered in a **single HTML file** with **zero API keys** required.

Designed to look and feel like a **military command center** — complete with CRT scan lines, HUD corner brackets, animated crosshair loading, and a cyan-on-black tactical aesthetic.

> **Why?** Because civilians deserve access to the same situational awareness tools that were once reserved for operations rooms. VARTA democratizes real-time threat intelligence using nothing but publicly available data.

---

## Features

<table>
<tr>
<td width="50%">

### 🛰️ Satellite Fire Detection
NASA FIRMS (VIIRS) thermal anomaly data. Detects active fires, infrastructure hits, and explosions visible from space — updated every few hours.

### 📡 Real-Time Air Raid Alerts
Live siren data across all 26 Ukrainian oblasts. Color-coded by threat confirmation level. Oblast-level and city-level precision.

### 🔴 Frontline Mapping
Daily GeoJSON polygons from [DeepStateMap](https://github.com/cyterat/deepstate-map-data) showing Russian-occupied territory. Bright red frontline borders with semi-transparent occupied zones.

</td>
<td width="50%">

### 🌍 Seismic Monitoring
USGS earthquake data filtered for Ukraine's bounding box. Helps distinguish between natural seismic events and potential military explosions.

### 🌫️ Air Quality Tracking
Real-time PM2.5 and PM10 levels across 6 major Ukrainian cities via Open-Meteo. Critical for assessing post-strike environmental impact.

### 📰 Live News Feed
Auto-aggregated English-language news from Ukrainska Pravda and UNIAN. Severity-classified and sorted by priority. Click to read full articles.

</td>
</tr>
</table>

### And more...

- **🔗 Cross-Source Correlation** — When multiple sources confirm the same event (e.g., active alert + satellite fire + seismic activity), VARTA automatically escalates to `CONFIRMED IMPACT`
- **🔔 Browser Notifications** — Critical events trigger desktop push notifications
- **🔊 Audio Alerts** — Audible warning tones for high-severity events
- **🗺️ 48 City Coordinates** — Precise city-level incident markers, not just oblast blobs
- **💾 Persistent Settings** — All preferences saved to localStorage across sessions
- **📱 Responsive Layout** — Adapts from desktop (60/40 split) to tablet to mobile

---

## How It Works

```
                        ┌─────────────────────────────────────┐
                        │          VARTA DASHBOARD            │
                        │    (Pure client-side JavaScript)     │
                        └──────────────┬──────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼──────┐
              │  ALERT     │    │  SATELLITE  │    │  FRONTLINE │
              │  SOURCES   │    │  & SENSOR   │    │  MAPPING   │
              │            │    │             │    │            │
              │ alerts.in  │    │ NASA FIRMS  │    │ DeepState  │
              │ .ua API    │    │ USGS Seismic│    │ GitHub     │
              │ Pravda RSS │    │ Open-Meteo  │    │ GeoJSON    │
              │ UNIAN RSS  │    │ AQ API      │    │            │
              └─────┬──────┘    └──────┬──────┘    └─────┬──────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  CORRELATION    │
                              │  ENGINE         │
                              │                 │
                              │ Cross-reference │
                              │ alerts + fires  │
                              │ + seismic data  │
                              │ → CONFIRM or    │
                              │   ESCALATE      │
                              └────────┬────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        │              │              │
                  ┌─────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
                  │ LEAFLET   │ │ LIVE FEED  │ │ NOTIF &  │
                  │ MAP       │ │ PANEL      │ │ AUDIO    │
                  │           │ │            │ │ ALERTS   │
                  │ 6 overlay │ │ Severity-  │ │          │
                  │ layers    │ │ sorted     │ │ Desktop  │
                  │ + markers │ │ + filtered │ │ push +   │
                  │ + popups  │ │ + linked   │ │ beep     │
                  └───────────┘ └────────────┘ └──────────┘
```

**CORS Strategy:** Public APIs that lack CORS headers are accessed through a fallback proxy chain (`allorigins.win` → `corsproxy.io`). GitHub raw content is fetched directly.

---

## Data Sources

| Source | Provider | What It Detects | Update Frequency | API Key? |
|--------|----------|----------------|-----------------|----------|
| **Air Raid Alerts** | [alerts.in.ua](https://alerts.in.ua) | Active air raid sirens across 26 oblasts | Real-time | No |
| **News** | [Ukrainska Pravda](https://www.pravda.com.ua/eng/) + [UNIAN](https://www.unian.net/) | Breaking news, classified by severity | RSS refresh | No |
| **Fire Detection** | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) | Satellite thermal anomalies (VIIRS/NOAA-20) | Every 3-6 hours | Optional* |
| **Seismic** | [USGS Earthquake API](https://earthquake.usgs.gov/) | Magnitude 1.0+ events in Ukraine bbox | Real-time | No |
| **Air Quality** | [Open-Meteo](https://open-meteo.com/) | PM2.5 and PM10 in 6 major cities | Every 15 min | No |
| **Frontline** | [DeepStateMap](https://github.com/cyterat/deepstate-map-data) | Russian-occupied territory polygons | Daily @ 03:00 UTC | No |

*\* NASA FIRMS works without a key but a free [MAP_KEY](https://firms.modaps.eosdis.nasa.gov/api/area/) unlocks full data access. Enter it directly in the dashboard UI.*

---

## Quick Start

**Option 1 — Just open it:**

```bash
git clone https://github.com/clmrie/varta.git
open varta/index.html
```

That's it. No `npm install`. No build step. No environment variables. Just a browser.

**Option 2 — GitHub Pages (recommended for sharing):**

1. Fork this repo
2. Go to **Settings → Pages**
3. Set source to **Deploy from branch → `main` → `/ (root)`**
4. Your live dashboard will be at `https://yourusername.github.io/varta`

**Option 3 — Any static host:**

Upload `index.html` to Netlify, Vercel, Cloudflare Pages, S3, or any web server. It's one file.

---

## Configuration

All settings are controlled directly in the dashboard UI and persisted to `localStorage`:

| Setting | Where | Description |
|---------|-------|-------------|
| **Layer Toggles** | Top-right of map | Toggle Frontline / Fires / Seismic / Air Quality on/off |
| **Auto-Refresh** | Bottom bar | 1 min, 2 min (default), 5 min, 10 min, or off |
| **FIRMS API Key** | Bottom bar | Optional NASA MAP_KEY for satellite fire data |
| **Notifications** | Bottom bar | Enable/disable browser push notifications |
| **Audio Alerts** | Bottom bar | Enable/disable audible alert tones |

---

## Tech Stack

```
HTML ─── Single file, ~95KB
CSS ──── Custom surveillance theme (scan lines, HUD, CRT glow)
JS ───── Vanilla ES6+ (no framework, no transpiler)
Map ──── Leaflet.js v1.9.4 (only external dependency)
Build ── None. Zero. Nada. Just open the file.
```

**Why a single file?** Because the best deployment strategy is no deployment strategy. One file means:
- Works offline after first load
- Copy to a USB drive for areas with limited connectivity
- No dependency hell, no breaking changes, no supply chain attacks
- Anyone can audit the entire codebase in one read

---

## The UI

VARTA's interface is designed as a **tactical operations center**:

- **CRT scan lines** — Subtle horizontal lines across the entire viewport
- **Cyan-on-black palette** — `#00e5ff` accents on `#030608` backgrounds
- **HUD corner brackets** — L-shaped cyan markers on the feed panel
- **Animated crosshair** — Pulsing `+` with rotating ring during data acquisition
- **Map grid overlay** — 60px cyan tactical grid over the map
- **Edge vignette** — Radial darkening that focuses attention on the center
- **Scanning border** — Animated gradient that sweeps across the alert banner
- **Monospace everything** — All data text uses monospace fonts with letter-spacing
- **Zero border-radius** — Angular, sharp corners everywhere. No rounded buttons.
- **Glow effects** — Text shadows and box shadows in cyan, green, and red

---

## Contributing

Contributions are welcome! Some ideas:

- **New data sources** — Satellite imagery, weather conditions, radiation monitoring
- **Historical tracking** — Frontline movement over time with date slider
- **Improved classification** — Better NLP for news severity detection
- **Localization** — Ukrainian and other language support
- **Mobile optimization** — Better touch interactions for map
- **Accessibility** — Screen reader support, high contrast mode

```bash
# Fork → Clone → Branch → Code → PR
git checkout -b feature/your-feature
# Make your changes to index.html
# Open in browser to test
# Submit a pull request
```

---

## Disclaimer

> VARTA is an **informational tool** that aggregates publicly available data. It is **not** a military-grade intelligence system. Data accuracy depends entirely on upstream sources (alerts.in.ua, NASA, USGS, DeepStateMap, etc.). Frontline positions are approximate and updated daily, not in real-time. **Do not make safety-critical decisions based solely on this dashboard.** Always follow official emergency instructions from Ukrainian authorities.

---

## License

[MIT](LICENSE) — Use it, fork it, deploy it, improve it. Free as in freedom.

---

<div align="center">

🇺🇦

**Слава Україні! / Glory to Ukraine!**

*Built with open data and open hearts.*

<sub>VARTA (Варта) — "The Guard" — Standing watch so you don't have to.</sub>

</div>
