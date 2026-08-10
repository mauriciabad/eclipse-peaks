import json, math, numpy as np
from PIL import Image
import lightpol as L

g=L.load(2025)
M=json.load(open('base_meta.json'))
Z,TS=M['Z'],M['TS']; N=(2**Z)*TS
MOSX,MOSY=1022*TS,752*TS

W,H=M['img_w'],M['img_h']
i=np.arange(W)+0.5; j=np.arange(H)+0.5
gx=MOSX+M['px_x0']+i*M['crop_w']/W
gy=MOSY+M['px_y0']+j*M['crop_h']/H
lon=gx/N*360-180
lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*gy/N))))
LON,LAT=np.meshgrid(lon,lat)

c=LON*120-0.5; r=(LAT-40)*120-0.5
c0=np.clip(np.floor(c).astype(int),0,598); r0=np.clip(np.floor(r).astype(int),0,598)
fc=np.clip(c-c0,0,1); fr=np.clip(r-r0,0,1)
val=(g[r0,c0]*(1-fc)*(1-fr)+g[r0,c0+1]*fc*(1-fr)
     +g[r0+1,c0]*(1-fc)*fr+g[r0+1,c0+1]*fc*fr)
ratio=L.ratio(val); mp=L.mpsas(ratio)
print('overlay mpsas range %.2f .. %.2f'%(mp.min(),mp.max()))

# perceptual ramp keyed to sky brightness: dark sky = transparent, bright = magenta/white
stops=[(21.9,(30,40,90),0),(21.3,(60,50,140),40),(20.6,(140,60,150),85),
       (19.9,(210,80,110),125),(19.2,(245,140,70),165),(18.5,(255,200,90),200),(17.2,(255,250,225),235)]
rgba=np.zeros((H,W,4),np.float32)
xs=[s[0] for s in stops]
for k in range(len(stops)-1):
    a,b=stops[k],stops[k+1]
    m=(mp<=a[0])&(mp>b[0]) if k<len(stops)-2 else (mp<=a[0])
    t=np.clip((a[0]-mp)/(a[0]-b[0]),0,1)[m][:,None]
    rgba[m,:3]=np.array(a[1])*(1-t)+np.array(b[1])*t
    rgba[m,3]=(a[2]*(1-t[:,0])+b[2]*t[:,0])
rgba[mp>21.9,3]=0
out=np.clip(rgba,0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save('lp.png',optimize=True)
print('lp.png written', Image.open('lp.png').size)

# per-peak values
d=json.load(open('peaks_computed_all.json'))
lpv={}
for p in d['peaks']:
    cc=L.sample(g,p['lat'],p['lon']); rr=float(L.ratio(cc)); mm=float(L.mpsas(rr))
    b=(1 if mm>=21.99 else 2 if mm>=21.89 else 3 if mm>=21.69 else 4 if mm>=20.49
       else 5 if mm>=19.50 else 6 if mm>=18.94 else 7 if mm>=18.38 else 8 if mm>=17.80 else 9)
    lpv[p['id']]=[round(mm,2),b]
json.dump(lpv,open('lp_peaks.json','w'))
import collections
print('peak Bortle histogram:',dict(sorted(collections.Counter(v[1] for v in lpv.values()).items())))
