import gzip, numpy as np

def load(year=2025):
    raw=np.frombuffer(gzip.open(f'lp_{year}.dat.gz','rb').read(),dtype=np.int8).astype(np.int32)
    assert raw.size==360001, raw.size
    first=128*int(raw[0])+int(raw[1])
    d=raw[1:].reshape(600,600).copy()      # element (r,c) -> raw[600*r+1+c]
    d[0,0]=0
    row0=first+np.cumsum(d[:,0])-d[0,0]    # walk down column 0
    row0[0]=first
    g=d.copy(); g[:,0]=0
    grid=row0[:,None]+np.cumsum(g,axis=1)  # then across each row
    return grid                            # compressed values, [row=lat, col=lon]

def ratio(c):  return (5.0/195.0)*(np.exp(0.0195*c)-1.0)
def mpsas(r):  return 22.0-5.0*np.log(1.0+r)/np.log(100.0)
def bortle(r):
    # djlorenz zone thresholds on brightness ratio
    edges=[0.01,0.06,0.11,0.19,0.33,0.58,1.0,1.73,3.0,5.2,9.0,15.6,27.0]
    return int(np.searchsorted(edges,r))+1

# grid geo: lon = (c+0.5)/120 ; lat = 40 + (r+0.5)/120
def sample(grid,lat,lon):
    c=lon*120-0.5; r=(lat-40)*120-0.5
    c0,r0=int(np.floor(c)),int(np.floor(r)); fc,fr=c-c0,r-r0
    v=(grid[r0,c0]*(1-fc)*(1-fr)+grid[r0,c0+1]*fc*(1-fr)
       +grid[r0+1,c0]*(1-fc)*fr+grid[r0+1,c0+1]*fc*fr)
    return v

if __name__=='__main__':
    g=load()
    print('grid',g.shape,'range',g.min(),g.max())
    for nm,la,lo in [('Barcelona',41.3874,2.1686),('Girona city',41.9794,2.8214),
                     ('Palamos',41.8478,3.1291),('Puig de Son Ric',41.9474,3.2088),
                     ('Turo de l Home',41.7691,2.4344),('Puigmal',42.3833,2.1167),
                     ('deep Pyrenees',42.45,1.05)]:
        c=sample(g,la,lo); r=ratio(c)
        print(f'  {nm:16s} ratio {r:7.2f}  {mpsas(r):5.2f} mag/arcsec2  Bortle ~{bortle(r)}')
