import math, numpy as np
from PIL import Image

Z=11; N=2**Z; TS=256
X0,X1,Y0,Y1 = 1022,1043,752,765

def build():
    W=(X1-X0+1)*TS; H=(Y1-Y0+1)*TS
    dem=np.full((H,W), np.nan, dtype=np.float32)
    for tx in range(X0,X1+1):
        for ty in range(Y0,Y1+1):
            im=Image.open(f'tiles/{tx}_{ty}.png').convert('RGB')
            a=np.asarray(im).astype(np.float32)
            e=(a[:,:,0]*256 + a[:,:,1] + a[:,:,2]/256) - 32768
            dem[(ty-Y0)*TS:(ty-Y0+1)*TS, (tx-X0)*TS:(tx-X0+1)*TS]=e
    return dem

def lonlat_to_px(lon, lat):
    """global pixel coords -> local array coords"""
    x = (lon+180.0)/360.0*N*TS
    s = np.sin(np.radians(lat)); s=np.clip(s,-0.9999,0.9999)
    y = (0.5 - np.log((1+s)/(1-s))/(4*math.pi))*N*TS
    return x - X0*TS, y - Y0*TS

if __name__=='__main__':
    dem=build()
    np.save('dem.npy', dem)
    print('dem shape', dem.shape, 'min', np.nanmin(dem), 'max', np.nanmax(dem))
    # sanity: Puigmal 42.3830,2.1170 should be ~2900
    for nm,la,lo,exp in [('Puigmal',42.3830,2.1170,2910),('Montseny/TuroHome',41.7756,2.4056,1706),('Palamos',41.8478,3.1291,10)]:
        x,y=lonlat_to_px(lo,la)
        print(f'{nm:18s} dem={dem[int(round(y)),int(round(x))]:8.1f}  expected~{exp}')
