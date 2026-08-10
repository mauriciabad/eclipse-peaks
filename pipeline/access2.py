"""Nearest road/track per summit, with ascent from that point and a Naismith walking time."""
import json, math, numpy as np
import dem as D

DRIVE = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service'}
demA = np.load('dem.npy'); DH, DW = demA.shape

r = json.load(open('roads2.json'))
dl, tr = [], []
for w in r['elements']:
    hw = w.get('tags', {}).get('highway')
    g = w.get('geometry')
    if not g:
        continue
    tgt = dl if hw in DRIVE else (tr if hw == 'track' else None)
    if tgt is None:
        continue
    for p in g:
        tgt.append((p['lat'], p['lon']))
dl = np.array(dl); tr = np.array(tr)
print('drivable nodes', len(dl), 'track nodes', len(tr))

LAT0 = 42.0; MPD = 111320.0; MPDL = MPD*math.cos(math.radians(LAT0))
D_ = np.stack([dl[:,0]*MPD, dl[:,1]*MPDL], 1)
T_ = np.stack([tr[:,0]*MPD, tr[:,1]*MPDL], 1)
CELL = 1000.0

def grid(P):
    g = {}
    k = np.floor(P/CELL).astype(np.int32)
    for i, (a, b) in enumerate(k):
        g.setdefault((a, b), []).append(i)
    return {kk: np.array(vv) for kk, vv in g.items()}

GD, GT = grid(D_), grid(T_)

def nearest(P, G, y, x, maxr=8):
    a0, b0 = int(math.floor(y/CELL)), int(math.floor(x/CELL))
    for rad in range(maxr+1):
        idx = []
        for a in range(a0-rad, a0+rad+1):
            for b in range(b0-rad, b0+rad+1):
                if rad and max(abs(a-a0), abs(b-b0)) != rad:
                    continue
                if (a, b) in G:
                    idx.append(G[(a, b)])
        if idx:
            I = np.concatenate(idx)
            d = np.hypot(P[I,0]-y, P[I,1]-x)
            j = int(np.argmin(d))
            if d[j] <= (rad+1)*CELL or rad == maxr:
                return float(d[j]), int(I[j])
    return None, None

def dem_at(lat, lon):
    x, y = D.lonlat_to_px(np.array([lon]), np.array([lat]))
    xi, yi = int(round(float(x[0]))), int(round(float(y[0])))
    if 0 <= xi < DW and 0 <= yi < DH:
        v = demA[yi, xi]
        return None if np.isnan(v) else float(v)
    return None

def naismith(dist_m, ascent_m):
    """4 km/h on the flat plus one hour per 600 m of climb; minimum one minute."""
    return max(1.0, (dist_m/4000.0 + max(0.0, ascent_m)/600.0)*60.0)

pk = json.load(open('all_peaks.json'))
res = {}
for p in pk:
    y, x = p['lat']*MPD, p['lon']*MPDL
    out = {}
    for key, P, G, src in (('road', D_, GD, dl), ('track', T_, GT, tr)):
        d, j = nearest(P, G, y, x)
        if d is None:
            out[key] = None; continue
        e = dem_at(src[j][0], src[j][1])
        asc = None if e is None else max(0.0, p['ele'] - e)
        out[key] = {'m': round(d), 'ele': None if e is None else round(e),
                    'asc': None if asc is None else round(asc),
                    'min': round(naismith(d, asc if asc is not None else 0))}
    res[p['id']] = out
json.dump(res, open('access2.json', 'w'))

ok = [v['road']['m'] for v in res.values() if v.get('road')]
print('computed', len(res), '| median road dist %.0f m' % np.median(ok))
