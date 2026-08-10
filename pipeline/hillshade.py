import math, numpy as np, dem as D
from PIL import Image

demA=np.load('dem.npy')
# region of interest in lon/lat
LO0,LA1,LO1,LA0 = 2.18, 42.50, 3.40, 41.58   # left, top, right, bottom
x0,y0 = D.lonlat_to_px(LO0,LA1); x1,y1 = D.lonlat_to_px(LO1,LA0)
x0,y0,x1,y1 = int(x0),int(y0),int(math.ceil(x1)),int(math.ceil(y1))
sub=demA[y0:y1, x0:x1].astype(np.float32)
print('crop px',sub.shape, 'origin',x0,y0)

# pixel ground size (Mercator scale correction at this latitude)
latc=(LA0+LA1)/2
res = 156543.03392*math.cos(math.radians(latc))/(2**11)/256*256  # m per px at z11
res = 40075016.686*math.cos(math.radians(latc))/(2**11*256)
print('ground res %.1f m/px'%res)

z=sub.copy(); sea = z<=0
z=np.where(sea,0,z)
gy,gx=np.gradient(z,res,res)
slope=np.arctan(np.hypot(gx,gy)); aspect=np.arctan2(-gx,gy)
def shade(az_deg,alt_deg):
    az=math.radians(360-az_deg+90); alt=math.radians(alt_deg)
    v=(np.sin(alt)*np.cos(slope) + np.cos(alt)*np.sin(slope)*np.cos(az-aspect))
    return np.clip(v,0,1)
hs = 0.6*shade(315,45)+0.4*shade(287,12)   # NW key light + low WNW light (the eclipse direction)
hs = np.clip(hs*1.15,0,1)

# hypsometric tint
stops=[(0,(198,214,180)),(250,(168,196,140)),(600,(206,200,136)),(1100,(198,166,110)),
       (1700,(180,140,110)),(2300,(196,186,182)),(2950,(246,246,248))]
zc=np.clip(z,0,2950)
rgb=np.zeros(sub.shape+(3,),np.float32)
for i in range(len(stops)-1):
    e0,c0=stops[i]; e1,c1=stops[i+1]
    m=(zc>=e0)&(zc<=e1); t=((zc-e0)/(e1-e0))[m][:,None]
    rgb[m]=np.array(c0)*(1-t)+np.array(c1)*t
img=rgb*(0.35+0.75*hs[:,:,None])
img[sea]=np.array([26,48,74])*(1.0)          # sea
out=np.clip(img,0,255).astype(np.uint8)
im=Image.fromarray(out)
im.thumbnail((1500,1500),Image.LANCZOS)
im.save('base.png',optimize=True)
print('image',im.size)
meta={'px_x0':x0,'px_y0':y0,'crop_w':x1-x0,'crop_h':y1-y0,'img_w':im.size[0],'img_h':im.size[1],'Z':11,'TS':256}
import json; json.dump(meta,open('base_meta.json','w')); print(meta)
