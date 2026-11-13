"""Crown Squid (issue #74 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A large crimson squid jetting mantle-first to the north, with three
pointed fin lobes each side forming a crown at the mantle tip, eight arms and two long
clubbed tentacles trailing south."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("squid", {
    "body": "#b3243c", "dark": "#7d1630", "belly": "#e58a8f", "fin": "#d6475a",
    "arm": "#a11f37", "club": "#f0a0a0", "eye": "#f0d68c", "pupil": "#0b0612",
})
ZC = 0.85
S = [0.0, 0.06, 0.2, 0.42, 0.66, 0.86, 1.0]
W = [0.0, 0.16, 0.36, 0.52, 0.58, 0.54, 0.44]
TIP, LEN = 2.6, 2.9
ring_of = lambda y: int((TIP - y) / 0.36)
loft([{"y": TIP - LEN * s, "w": w, "h": w * 0.82, "b": w * 0.6, "z": ZC} for s, w in zip(S, W)],
     "body", sides=10, belly="belly", name="mantle",
     paint=lambda p: "dark" if p.normal.z > 0.5 and ring_of(p.center.y) % 2 == 1 and p.center.y < 1.9 else None)
for side in (-1, 1):
    # the crown: three swept points down each side of the mantle tip
    plate([(side * 0.05, 2.58, ZC), (side * 0.62, 2.72, ZC), (side * 0.42, 2.2, ZC), (side * 1.05, 2.2, ZC), (side * 0.66, 1.66, ZC),
           (side * 1.25, 1.5, ZC), (side * 0.7, 1.02, ZC), (side * 0.5, 0.7, ZC), (side * 0.42, 1.5, ZC), (side * 0.2, 2.2, ZC)], 0.06, "fin", name="crown")
    eye((side * 0.4, -0.62, ZC + 0.08), 0.17, (side * 0.85, 0.0, 0.5))
    for k, (x0, dz, ln, fan) in enumerate(((0.07, 0.06, 1.9, 0.25), (0.2, 0.04, 1.75, 0.7), (0.12, -0.08, 1.55, 0.5), (0.26, -0.07, 1.4, 1.05))):
        pts = [(side * (x0 + fan * t * t) + 0.06 * math.sin(4 * t + k), -0.95 - ln * t, ZC - 0.03 + dz * (1 - 0.4 * t)) for t in (i / 6 for i in range(7))]
        tube(pts, [0.1, 0.09, 0.075, 0.06, 0.045, 0.03, 0.0], "arm", sides=4, flat=0.8, name="arm",
             paint=lambda p: "belly" if p.normal.z < -0.3 else None)
    # the long feeding tentacle with a flat club
    pts = [(side * (0.16 + 1.25 * t ** 1.5) + 0.1 * math.sin(5 * t + side), -0.95 - 3.6 * t, ZC - 0.05) for t in (i / 9 for i in range(10))]
    tube(pts, [0.07, 0.06, 0.055, 0.05, 0.05, 0.045, 0.045, 0.05, 0.06, 0.05], "arm", sides=4, name="tentacle")
    gem((pts[-1][0] + side * 0.03, pts[-1][1] - 0.2, ZC - 0.05), (0.13, 0.36, 0.07), "club", name="club")
loft([{"y": -0.22, "w": 0.4, "h": 0.33, "b": 0.26, "z": ZC}, {"y": -0.6, "w": 0.42, "h": 0.33, "b": 0.26, "z": ZC},
      {"y": -1.0, "w": 0.3, "h": 0.22, "b": 0.2, "z": ZC}], "body", sides=8, belly="belly", name="head")
finish("crown_squid", ASSETS + "/creature-crown-squid")
