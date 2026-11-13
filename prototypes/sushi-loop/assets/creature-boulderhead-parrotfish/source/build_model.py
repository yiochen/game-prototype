"""Boulderhead Parrotfish (issue #76 concept, low-poly). Run in Blender with ASSETS set
to this assets folder. A deep-bodied teal parrotfish swimming north, with a heavy
pale boulder of a forehead, a cream beak, checkered scales and pink fins."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("parrot", {
    "body": "#1f9c9a", "scale": "#4cc7b0", "belly": "#f4a7b5", "bump": "#8fcfc0", "crack": "#5fa898",
    "beak": "#f6ecd2", "fin": "#e85a9b", "pec": "#f2c84b", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 1.05
Y = [1.95, 1.7, 1.2, 0.5, -0.3, -1.0, -1.6, -1.95]
W = [0.24, 0.52, 0.74, 0.78, 0.66, 0.44, 0.22, 0.14]
H = [0.3, 0.62, 0.84, 0.88, 0.76, 0.5, 0.28, 0.2]
def paint(p):
    if p.normal.z < -0.45: return "belly"
    col = int((math.atan2(p.center.x, p.center.z - ZC) + math.pi) / (2 * math.pi / 10))
    row = int((2.0 - p.center.y) / 0.36)
    return "scale" if (row + col) % 2 == 0 and p.center.y < 1.3 else None
st = []
for i in range(len(Y) - 1):                           # extra rings so the scales read as a checker
    for k in range(2):
        t = k / 2
        st.append({"y": Y[i] + (Y[i + 1] - Y[i]) * t, "w": W[i] + (W[i + 1] - W[i]) * t, "h": H[i] + (H[i + 1] - H[i]) * t, "z": ZC})
st.append({"y": Y[-1], "w": W[-1], "h": H[-1], "z": ZC})
loft(st, "body", sides=10, paint=paint, name="body")
gem((0, 1.5, ZC + 0.62), (0.5, 0.56, 0.46), "bump", name="boulder",
    paint=lambda p: "crack" if p.normal.y > 0.75 else None)
gem((0, 2.0, ZC - 0.08), (0.24, 0.2, 0.26), "beak", name="beak")
h_at = lambda y: lerp_tab(-y, [-v for v in Y], H)
strip([(0, y, ZC + h_at(y) - 0.04) for y in (1.0, 0.5, 0.0, -0.5, -1.0, -1.4)],
      [(0, y - 0.12, ZC + h_at(y) + r) for y, r in zip((1.0, 0.5, 0.0, -0.5, -1.0, -1.4), (0.12, 0.34, 0.36, 0.34, 0.3, 0.1))], 0.06, "fin", name="dorsal")
plate([(0, -1.85, ZC + 0.16), (0, -2.75, ZC + 0.9), (0, -2.4, ZC), (0, -2.75, ZC - 0.9), (0, -1.85, ZC - 0.16)], 0.07, "fin", name="tail")
for side in (-1, 1):
    eye((side * 0.6, 1.5, ZC + 0.12), 0.13, (side * 0.9, 0.15, 0.35))
    plate([(side * 0.7, 0.95, ZC - 0.05), (side * 1.3, 0.7, ZC + 0.22), (side * 1.4, 0.25, ZC + 0.2), (side * 1.2, -0.05, ZC + 0.1), (side * 0.72, 0.4, ZC - 0.1)], 0.05, "pec", name="pectoral")
    plate([(side * 0.3, -0.2, ZC - 0.7), (side * 0.55, -0.7, ZC - 0.95), (side * 0.25, -0.75, ZC - 0.7)], 0.05, "fin", name="pelvic")
finish("boulderhead_parrotfish", ASSETS + "/creature-boulderhead-parrotfish")
