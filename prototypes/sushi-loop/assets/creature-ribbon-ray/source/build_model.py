"""Ribbon Ray (issue #69 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A broad indigo diamond ray, nose north, with dashed pale spots along
each wing and two long ribbons trailing south."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("ray", {
    "back": "#2f2f8a", "edge": "#4a4fc0", "belly": "#cfd3f5", "spot": "#b9c2ff",
    "ribbon": "#6a5fd0", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 0.8
Y = [1.75, 1.5, 1.1, 0.6, 0.15, -0.3, -0.8, -1.2, -1.5]
W = [0.0, 0.34, 0.85, 1.6, 2.25, 1.55, 0.8, 0.36, 0.1]
H = [0.0, 0.12, 0.2, 0.25, 0.24, 0.22, 0.17, 0.11, 0.05]
# one flat lens: the wing tips sweep back a little
def paint(p):
    if p.normal.z < -0.3: return "belly"
    return "edge" if abs(p.center.x) > 0.62 * lerp_tab(-p.center.y, [-y for y in Y], W) else None
loft([{"y": y, "w": w, "h": h, "b": h * 0.6, "z": ZC} for y, w, h in zip(Y, W, H)], "back", sides=12, paint=paint, name="disc", offset=0.0)
def top(x, y):
    w, h = lerp_tab(-y, [-v for v in Y], W), lerp_tab(-y, [-v for v in Y], H)
    return ZC + h * math.sqrt(max(0.0, 1 - (x / w) ** 2)) if w > 0 else ZC
for side in (-1, 1):
    for k in range(6):                                # dashed spots from the shoulder to the wing tip
        t = k / 5
        x, y = side * (0.35 + 1.25 * t), 1.0 - 0.75 * t
        gem((x, y, top(x, y) + 0.01), (0.07, 0.11, 0.03), "spot", rot=Matrix.Rotation(side * math.radians(55), 4, "Z"), name="spot")
    for k in range(4):
        t = k / 3
        x, y = side * (0.3 + 0.25 * t), 0.35 - 1.2 * t
        gem((x, y, top(x, y) + 0.01), (0.06, 0.1, 0.03), "spot", name="spot")
    eye((side * 0.3, 1.18, top(side * 0.3, 1.18) + 0.02), 0.09, (side * 0.6, 0.2, 0.75))
    cone((side * 0.2, 1.55, ZC), (side * 0.3, 1.95, ZC - 0.02), 0.09, "edge", sides=4, name="lobe")
    plate([(side * 0.12, -1.35, ZC), (side * 0.5, -1.55, ZC), (side * 0.3, -1.85, ZC), (side * 0.08, -1.6, ZC)], 0.05, "edge", name="pelvic")
    pts, rad = [], []
    for k in range(13):                               # a long ribbon, waving
        t = k / 12
        pts.append((side * (0.1 + 0.35 * t) + 0.16 * math.sin(k * 0.95 + (0 if side > 0 else 1.6)), -1.45 - 3.0 * t, ZC - 0.05 * t))
        rad.append(0.12 * (1 - t) + 0.035 if k < 12 else 0.0)
    tube(pts, rad, "ribbon", sides=4, flat=0.3, name="ribbon")
finish("ribbon_ray", ASSETS + "/creature-ribbon-ray")
