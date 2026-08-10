# Últim Sol

Find where to stand for the **12 August 2026 solar eclipse at sunset** on the Costa Brava.

At maximum the Sun sits about **3.6° above the horizon at azimuth 287° (WNW)**. At that altitude
the thing that decides whether you see it is not how high your peak is — it is whether anything
along that one bearing is taller than 3.6° as seen from where you stand. This tool answers that
question for **2,451 summits** by tracing the real western skyline from each one.

> **Palamós is outside the path of totality.** The coast gets a 98.8% partial eclipse. Totality
> that evening crosses Tarragona and Lleida, roughly two hours away by car.

## What it computes

For every summit, from a 57 m/px digital elevation model:

- **Skyline profile** — terrain elevation angle across azimuth 275°–302°, ray-traced out to 220 km
  with Earth curvature and standard atmospheric refraction (effective radius 7/6 R).
- **Horizon clearance at maximum** — Sun altitude minus skyline height at the Sun's azimuth.
  Positive means you see it; negative means a ridge is in the way.
- **Terrain-aware sunset** — the moment the Sun's centre drops below the *actual* skyline,
  not the idealised flat horizon. Worth up to ten minutes.
- **Access** — straight-line distance to the nearest road or track a car can reach, with the
  ascent from that point, converted to a walking time by Naismith's rule.
- **Sky brightness** — light pollution in mag/arcsec² and Bortle class.

The Sun position routine is NOAA's algorithm; it reproduces
[ServiAstro](https://serviastro.ub.edu/en/phenomena/solar-eclipse/total-solar-eclipse-august-12th-2026)'s
published 3.8° altitude for Girona to within 0.03°.

## Running it

`index.html` is fully self-contained — the terrain basemap, the overlays and all summit data are
embedded. Open the file directly, or serve the folder:

```sh
python3 -m http.server 8000
```

### Publishing to GitHub Pages

Push to GitHub, then **Settings → Pages → Source: GitHub Actions**. The workflow in
`.github/workflows/pages.yml` publishes the repository root on every push to the default branch.

## Rebuilding the data

The `pipeline/` scripts regenerate everything from public sources. They need `numpy` and `pillow`.

| Script | Does |
| --- | --- |
| `sunpos.py` | NOAA solar position; validated against published eclipse circumstances |
| `dem.py` | Assembles the DEM from Terrarium terrain tiles |
| `hillshade.py` | Renders the shaded-relief basemap |
| `horizon.py` | Ray-traces skyline profiles and terrain-aware sunset times |
| `access.py` | Nearest road/track, ascent, and walking time |
| `lightpol.py` | Decodes the light pollution atlas binary tiles |
| `lp_overlay.py` | Renders the sky-brightness overlay |
| `roads_overlay.py` | Renders the road and track overlay |

Summit positions come from an Overpass query for `natural=peak` nodes carrying an `ele` tag.

## Data sources and licences

| Source | Used for | Licence |
| --- | --- | --- |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Summits, roads, tracks | ODbL |
| [Mapzen / AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) | Elevation (SRTM, EU-DEM and others) | see registry |
| [D. Lorenz, Light Pollution Atlas 2025](https://djlorenz.github.io/astronomy/lp/) | Sky brightness | credit the author |
| [ServiAstro (Universitat de Barcelona)](https://serviastro.ub.edu/) | Eclipse circumstances | — |

Elevations are OSM summit tags; the DEM is only used for the intervening terrain. The DEM sits a
median 19 m below tagged summit heights because 57 m pixels smooth sharp peaks, which makes the
computed clearances very slightly optimistic. Walk distances are straight-line, so treat them as a
lower bound on the real thing.
