#!/usr/bin/env python3
"""route-builder: convierte un .fit de una salida en Tempus Fugit en route.json para Fugit.

Uso: python route_builder.py actividad.fit -o route.json [--lap-start 2400]

- Detecta sola la longitud de vuelta (el tramo del trazado que se repite).
- Separa acceso (lead-in) y vuelta, remuestrea cada 2 m, suaviza la altitud
  y calcula la pendiente. El route.json resultante no se sube al repositorio.
"""
import argparse, json, math
import numpy as np
import fitdecode
from scipy.signal import savgol_filter

SEMI = 180 / 2**31
R = 6371000.0


def read_fit(path):
    lat, lon, alt = [], [], []
    with fitdecode.FitReader(path) as f:
        for fr in f:
            if isinstance(fr, fitdecode.FitDataMessage) and fr.name == "record":
                v = {fl.name: fl.value for fl in fr.fields}
                if v.get("position_lat") is None or v.get("position_long") is None:
                    continue
                a = v.get("enhanced_altitude", v.get("altitude"))
                lat.append(v["position_lat"] * SEMI)
                lon.append(v["position_long"] * SEMI)
                alt.append(a if a is not None else (alt[-1] if alt else 0.0))
    return np.array(lat), np.array(lon), np.array(alt, float)


def to_local(lat, lon):
    lat0, lon0 = lat[0], lon[0]
    x = np.radians(lon - lon0) * R * math.cos(math.radians(lat0))
    y = np.radians(lat - lat0) * R
    return np.c_[x, y], (float(lat0), float(lon0))


def cumdist(xy):
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]


def at(d, xy, s):
    return np.c_[np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])]


def detect_lap(d, xy, lo=5000, hi=40000, step=5):
    best = (None, float("inf"))
    for P in np.arange(lo, min(hi, d[-1] - 1000), step):
        s = np.arange(0, d[-1] - P, 10)
        e = np.median(np.linalg.norm(at(d, xy, s) - at(d, xy, s + P), axis=1))
        if e < best[1]:
            best = (float(P), float(e))
    return best


def resample(d, xy, alt, a, b, step=2.0):
    s = np.arange(a, b, step)
    p = at(d, xy, s)
    z = np.interp(s, d, alt)
    return s - a, p, z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fit")
    ap.add_argument("-o", "--out", default="route.json")
    ap.add_argument("--lap-start", type=float, default=2400.0, help="metros hasta el arco de meta")
    ap.add_argument("--name", default="Tempus Fugit")
    args = ap.parse_args()

    lat, lon, alt = read_fit(args.fit)
    xy, origin = to_local(lat, lon)
    d = cumdist(xy)
    lap, err = detect_lap(d, xy)
    if lap is None or err > 10 or args.lap_start + lap > d[-1]:
        raise SystemExit("No se encuentra una vuelta completa repetida en el .fit")

    # Suavizado de altitud sobre la serie original (Zwift la redondea y tiene picos)
    win = min(len(alt) // 2 * 2 - 1, 31)
    alt_s = savgol_filter(alt, win, 2)

    def section(a, b):
        s, p, z = resample(d, xy, alt_s, a, b)
        z = savgol_filter(z, 51, 2)
        g = np.gradient(z, s) * 100
        g = np.clip(savgol_filter(g, 101, 2), -3, 3)
        gain = float(np.sum(np.clip(np.diff(z), 0, None)))
        return {
            "length_m": round(float(s[-1]), 1),
            "elevation_gain_m": round(gain, 1),
            "points": [
                [round(float(si), 1), round(float(pi[0]), 2), round(float(pi[1]), 2), round(float(zi), 2), round(float(gi), 2)]
                for si, pi, zi, gi in zip(s, p, z, g)
            ],
        }

    out = {
        "name": args.name,
        "source": "fit",
        "origin_latlon": origin,
        "format": "points = [distancia_m, x_este_m, y_norte_m, altitud_m, pendiente_pct]",
        "step_m": 2.0,
        "lap_detection_error_m": round(err, 2),
        "lead_in": section(0, args.lap_start),
        "lap": section(args.lap_start, args.lap_start + lap),
        "landmarks": [
            {"name": "Meta (arco)", "lap_m": 0},
        ],
    }
    json.dump(out, open(args.out, "w"), separators=(",", ":"))
    print(f"{args.name}: acceso {out['lead_in']['length_m']/1000:.2f} km, "
          f"vuelta {out['lap']['length_m']/1000:.2f} km, desnivel vuelta {out['lap']['elevation_gain_m']:.0f} m, "
          f"error de detección {err:.1f} m -> {args.out}")


if __name__ == "__main__":
    main()
