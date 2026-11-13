"""Drum Jelly (issue #71 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A bell-shaped jellyfish swimming bell-first to the north, with glowing
concentric bands, frilled oral arms and thin tentacles trailing south."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("jelly", {
    "bell": "#8fc4f2", "cap": "#b9dcfa", "band": ("#ff6fd0", "#ff4fc8", 1.6), "band2": ("#7af0ff", "#4fe6ff", 1.4),
    "rim": "#5f8fe0", "under": "#4a63b8", "arm": "#c2a8f5", "tentacle": "#7f9cf0",
})
ZC = 1.0
Y = [1.4, 1.3, 1.08, 0.78, 0.48, 0.2, -0.02, -0.2, -0.12]
W = [0.0, 0.42, 0.82, 1.08, 1.22, 1.28, 1.24, 1.08, 0.5]
def paint(p):
    y = p.center.y
    if p.normal.y < -0.6 or y < -0.12: return "under"
    if y > 1.15: return "cap"
    if 0.5 < y < 0.8: return "band"
    if 0.0 < y < 0.2: return "band2"
    if y < 0.0: return "rim"
loft([{"y": y, "w": w, "h": w * 0.8, "z": ZC} for y, w in zip(Y, W)], "bell", sides=12, paint=paint, name="bell")
for k in range(4):                                    # frilled oral arms
    a = math.pi / 4 + k * math.pi / 2
    x0, z0 = 0.3 * math.sin(a), 0.22 * math.cos(a)
    pts = [(x0 * (1 + 0.5 * t) + 0.12 * math.sin(5 * t + k), -0.1 - 1.9 * t, ZC + z0 * (1 + 0.4 * t)) for t in (i / 6 for i in range(7))]
    tube(pts, [0.16, 0.19, 0.15, 0.17, 0.12, 0.1, 0.0], "arm", sides=4, name="oral_arm")
for k in range(10):                                   # thin tentacles from the rim
    a = 2 * math.pi * (k + 0.5) / 10
    x0, z0 = 1.0 * math.sin(a), 0.78 * math.cos(a)
    ln = 2.6 + 0.5 * math.sin(k * 2.3)
    pts = [(x0 * (1 - 0.25 * t) + 0.1 * math.sin(6 * t + k * 1.7), -0.15 - ln * t, ZC + z0 * (1 - 0.3 * t)) for t in (i / 7 for i in range(8))]
    tube(pts, [0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02, 0.0], "tentacle", sides=3, name="tentacle")
finish("drum_jelly", ASSETS + "/creature-drum-jelly")
