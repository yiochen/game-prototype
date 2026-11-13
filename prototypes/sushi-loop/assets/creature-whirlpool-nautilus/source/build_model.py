"""Whirlpool Nautilus (issue #73 concept, low-poly). Run in Blender with ASSETS set to
this assets folder. A coiled cream shell with rust stripes leads north; the hood, eye
and teal tentacles trail south. The shell is rolled over so the pursuit camera sees
the spiral."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("nautilus", {
    "shell": "#f6ead2", "stripe": "#c8552b", "hub": "#e9d3ae", "hood": "#b5532e",
    "hoodspot": "#f3dcb8", "tentacle": "#2fa7a0", "tentacle2": "#8fe0d0", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 1.05
A, B, T0, T1, N = 0.13, 0.19, 1.0 * math.pi, 3.5 * math.pi, 30
def centre(th):
    r = A * math.exp(B * th); phi = -(th - T1) - math.pi / 2      # ends below the hub, opening south
    return r, Vector((0, math.cos(phi), math.sin(phi)))
def ring(bm, th):
    r, e = centre(th)
    rho = 0.62 * r
    return [bm.verts.new(e * r + e * (math.cos(a) * rho) + Vector((math.sin(a) * rho * 0.95, 0, 0)))
            for a in (2 * math.pi * j / 10 for j in range(10))]
bms = [bmesh.new(), bmesh.new()]
for i in range(N):
    bm = bms[1 if i % 3 == 2 else 0]                              # every third band is a stripe
    ring_loft(bm, [ring(bm, T0 + (T1 - T0) * i / N), ring(bm, T0 + (T1 - T0) * (i + 1) / N)])
add(bms[0], "shell", None, "shell"); add(bms[1], "stripe", None, "stripes")
for side in (-1, 1):
    gem((side * 0.2, 0, 0), (0.12, 0.3, 0.3), "hub", name="hub")
r1, e1 = centre(T1)
mouth = e1 * r1
gem(mouth + Vector((0, -0.08, 0)), (0.62, 0.36, 0.62), "hood", name="hood")
gem(mouth + Vector((0, 0.0, 0.42)), (0.42, 0.28, 0.2), "hoodspot", name="hood_cap")
for side in (-1, 1):
    eye(mouth + Vector((side * 0.56, -0.14, 0.05)), 0.14, (side, -0.1, 0.1))
ROLL = Matrix.Translation((0, 0.55, ZC)) @ Matrix.Rotation(math.radians(52), 4, "Y")
turn(ROLL)
root = ROLL @ (mouth + Vector((0, -0.2, -0.05)))
for k in range(10):                                               # tentacles trail south, fanning
    a = 2 * math.pi * k / 10
    ox, oz = 0.32 * math.sin(a), 0.25 * math.cos(a)
    ln = 1.9 + 0.4 * math.sin(k * 1.9)
    pts = [(root.x + ox * (1 + 1.3 * t) + 0.07 * math.sin(5 * t + k), root.y - ln * t, root.z + oz * (1 + 0.5 * t) - 0.1 * t) for t in (i / 5 for i in range(6))]
    tube(pts, [0.085, 0.075, 0.06, 0.045, 0.03, 0.0], "tentacle" if k % 2 else "tentacle2", sides=4, name="tentacle")
finish("whirlpool_nautilus", ASSETS + "/creature-whirlpool-nautilus")
