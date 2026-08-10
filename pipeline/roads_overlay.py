"""Render roads and tracks as an overlay aligned to the hillshade basemap."""
import json, math, numpy as np
from PIL import Image, ImageDraw

M = json.load(open('base_meta.json'))
Z, TS = M['Z'], M['TS']; N = (2**Z)*TS
MOSX, MOSY = 1022*TS, 752*TS
W, H = M['img_w'], M['img_h']
SS = 2                                     # supersample for smoother lines

DRIVE = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service'}
MAJOR = {'motorway','trunk','primary'}
MINOR = {'secondary','tertiary'}


def proj(lon, lat):
    x = (lon+180)/360*N
    s = max(-.9999, min(.9999, math.sin(math.radians(lat))))
    y = (.5 - math.log((1+s)/(1-s))/(4*math.pi))*N
    return ((x-MOSX-M['px_x0'])*W/M['crop_w']*SS,
            (y-MOSY-M['px_y0'])*H/M['crop_h']*SS)


im = Image.new('RGBA', (W*SS, H*SS), (0, 0, 0, 0))
dr = ImageDraw.Draw(im)

# tracks underneath, then minor, then major on top
LAYERS = [
    (lambda hw: hw == 'track',  (150, 128, 96, 150), 1.1),
    (lambda hw: hw in DRIVE and hw not in MAJOR and hw not in MINOR, (206, 196, 172, 165), 1.2),
    (lambda hw: hw in MINOR,    (240, 226, 190, 205), 1.9),
    (lambda hw: hw in MAJOR,    (255, 236, 190, 235), 2.8),
]

data = json.load(open('roads2.json'))
els = data['elements']
print('ways:', len(els))
for test, col, wdt in LAYERS:
    n = 0
    for w in els:
        hw = w.get('tags', {}).get('highway')
        g = w.get('geometry')
        if not g or not test(hw):
            continue
        pts = [proj(p['lon'], p['lat']) for p in g]
        if len(pts) > 1:
            dr.line(pts, fill=col, width=max(1, int(round(wdt*SS))), joint='curve')
            n += 1
    print('  layer drawn:', n)

im = im.resize((W, H), Image.LANCZOS)
im.save('roads.png', optimize=True)
print('roads.png', im.size)
