import math
from datetime import datetime, timedelta, timezone

def julian(dt):
    dt = dt.astimezone(timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute/60 + dt.second/3600)/24
    if m <= 2: y -= 1; m += 12
    A = y//100; B = 2 - A + A//4
    return int(365.25*(y+4716)) + int(30.6001*(m+1)) + d + B - 1524.5

def sun_altaz(dt, lat, lon):
    """NOAA solar position algorithm. Returns (altitude_deg_refracted, azimuth_deg)."""
    jd = julian(dt); T = (jd - 2451545.0)/36525.0
    L0 = (280.46646 + T*(36000.76983 + T*0.0003032)) % 360
    M  = 357.52911 + T*(35999.05029 - 0.0001537*T)
    Mr = math.radians(M)
    C  = (math.sin(Mr)*(1.914602 - T*(0.004817 + 0.000014*T))
          + math.sin(2*Mr)*(0.019993 - 0.000101*T) + math.sin(3*Mr)*0.000289)
    true_long = L0 + C
    omega = 125.04 - 1934.136*T
    app_long = true_long - 0.00569 - 0.00478*math.sin(math.radians(omega))
    e0 = (23 + (26 + ((21.448 - T*(46.8150 + T*(0.00059 - T*0.001813))))/60)/60)
    e  = e0 + 0.00256*math.cos(math.radians(omega))
    lam = math.radians(app_long); er = math.radians(e)
    dec = math.asin(math.sin(er)*math.sin(lam))
    ra  = math.atan2(math.cos(er)*math.sin(lam), math.cos(lam))
    # equation of time
    y = math.tan(er/2)**2
    L0r = math.radians(L0); ecc = 0.016708634 - T*(0.000042037 + 0.0000001267*T)
    eot = 4*math.degrees(y*math.sin(2*L0r) - 2*ecc*math.sin(Mr) + 4*ecc*y*math.sin(Mr)*math.cos(2*L0r)
                         - 0.5*y*y*math.sin(4*L0r) - 1.25*ecc*ecc*math.sin(2*Mr))
    utc = dt.astimezone(timezone.utc)
    tst = (utc.hour*60 + utc.minute + utc.second/60) + eot + 4*lon
    ha = math.radians((tst/4) - 180) if (tst/4 - 180) > -180 else math.radians(tst/4 + 180)
    ha = math.radians(((tst/4) - 180 + 180) % 360 - 180)
    phi = math.radians(lat)
    sin_alt = math.sin(phi)*math.sin(dec) + math.cos(phi)*math.cos(dec)*math.cos(ha)
    alt = math.degrees(math.asin(max(-1,min(1,sin_alt))))
    az = math.degrees(math.atan2(-math.sin(ha)*math.cos(dec),
                                 math.cos(phi)*math.sin(dec) - math.sin(phi)*math.cos(dec)*math.cos(ha))) % 360
    # atmospheric refraction
    if alt > -1:
        tr = math.tan(math.radians(alt))
        if alt > 5: R = 58.1/tr - 0.07/tr**3 + 0.000086/tr**5
        elif alt > -0.575: R = 1735 + alt*(-518.2 + alt*(103.4 + alt*(-12.79 + alt*0.711)))
        else: R = -20.774/tr
        alt += R/3600
    return alt, az

if __name__ == "__main__":
    CEST = timezone(timedelta(hours=2))
    for name, la, lo in [("Palamos",41.8478,3.1291), ("Girona",41.9794,2.8214), ("Barcelona",41.3874,2.1686)]:
        t = datetime(2026,8,12,20,28,7,tzinfo=CEST)
        alt, az = sun_altaz(t, la, lo)
        print(f"{name:10s} at 20:28:07 CEST -> alt {alt:5.2f}deg  az {az:6.2f}deg")
