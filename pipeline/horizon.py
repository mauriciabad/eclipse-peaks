import json, math, numpy as np, dem as D
from datetime import datetime, timedelta, timezone
from sunpos import sun_altaz

CEST = timezone(timedelta(hours=2))
R = 6371008.8
K = 7.0/6.0           # standard refraction: effective earth radius
demA = np.load('dem.npy')
H, W = demA.shape

# --- sun track on eclipse evening ---
track = []
t = datetime(2026,8,12,19,30,tzinfo=CEST)
while t <= datetime(2026,8,12,21,10,tzinfo=CEST):
    a,z = sun_altaz(t, 41.95, 2.9)
    track.append((t,a,z)); t += timedelta(seconds=20)
azs = [z for _,a,z in track if a > -1.0]
print(f'sun azimuth range while up: {min(azs):.1f} -> {max(azs):.1f}')

AZ = np.arange(275.0, 302.01, 0.5)                     # sunset arc
DIST = np.concatenate([np.arange(100,3000,60), np.arange(3000,25000,150),
                       np.arange(25000,220000,600)]).astype(np.float64)
print('azimuths',len(AZ),'dist samples',len(DIST))

azr = np.radians(AZ)[:,None]; dr = DIST[None,:]/R
sin_d, cos_d = np.sin(dr), np.cos(dr)
drop = (DIST**2)/(2*R*K)                               # curvature+refraction drop

def horizon_profile(lat, lon, obs_h):
    p1 = math.radians(lat); l1 = math.radians(lon)
    sp, cp = math.sin(p1), math.cos(p1)
    p2 = np.arcsin(sp*cos_d + cp*sin_d*np.cos(azr))
    l2 = l1 + np.arctan2(np.sin(azr)*sin_d*cp, cos_d - sp*np.sin(p2))
    x, y = D.lonlat_to_px(np.degrees(l2), np.degrees(p2))
    xi = np.round(x).astype(np.int32); yi = np.round(y).astype(np.int32)
    ok = (xi>=0)&(xi<W)&(yi>=0)&(yi<H)
    h = np.where(ok, demA[np.clip(yi,0,H-1), np.clip(xi,0,W-1)], -1e6)
    ang = np.degrees(np.arctan2(h - obs_h - drop[None,:], DIST[None,:]))
    return ang.max(axis=1)                              # max angle per azimuth

peaks = json.load(open('girona_peaks.json'))
PAL = (41.8478, 3.1291)

def haversine(la1,lo1,la2,lo2):
    p1,p2=math.radians(la1),math.radians(la2)
    dp=p2-p1; dl=math.radians(lo2-lo1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))/1000

out=[]
for i,p in enumerate(peaks):
    obs = p['ele'] + 1.7
    prof = horizon_profile(p['lat'], p['lon'], obs)
    # walk the sun down; find last time it is above the terrain horizon
    last_vis=None; alt_max=None; hor_max=None
    for t,_,_ in track:
        a,z = sun_altaz(t, p['lat'], p['lon'])
        hz = float(np.interp(z, AZ, prof))
        if t.hour==20 and t.minute==28 and t.second==0:
            alt_max, hor_max = a, hz
        if a > hz: last_vis = t
    # flat-horizon (sea) sunset for comparison
    flat=None
    dip = -math.degrees(math.acos(min(1.0, R/(R+max(p['ele'],0)))))
    for t,_,_ in track:
        a,_ = sun_altaz(t, p['lat'], p['lon'])
        if a > dip - 0.27: flat = t
    out.append({**p,
        'dist_pal': round(haversine(*PAL, p['lat'], p['lon']),1),
        'sunset': last_vis.strftime('%H:%M:%S') if last_vis else None,
        'sunset_flat': flat.strftime('%H:%M:%S') if flat else None,
        'sun_alt_max': round(alt_max,2) if alt_max is not None else None,
        'hor_max': round(hor_max,2) if hor_max is not None else None,
        'clear_max': round(alt_max-hor_max,2) if alt_max is not None else None,
        'prof': [round(float(v),2) for v in prof]})
    if i%200==0: print(' ',i,flush=True)

json.dump({'az':list(AZ),'peaks':out}, open('peaks_computed.json','w'))
print('done', len(out))
