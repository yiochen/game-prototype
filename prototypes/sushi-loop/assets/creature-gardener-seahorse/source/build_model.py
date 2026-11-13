"""Gardener Seahorse (issue #77 concept, low-poly). Run in Blender with ASSETS set to
this assets folder. An orange seahorse with leaf-green fins. A seahorse swims upright,
which the pursuit camera would see as a dot, so the model lies in its side profile:
head north, coiled tail south, snout and belly to the east (+X), back fin west."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("seahorse", {
    "body": "#f39a1f", "band": "#d9741a", "belly": "#ffd27a", "ridge": "#b85a14",
    "leaf": "#57b84a", "leaf2": "#9be06a", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 0.75
SP = [(0.05, 1.5), (-0.06, 1.15), (0.05, 0.8), (0.24, 0.4), (0.22, 0.0), (0.06, -0.4), (-0.1, -0.8), (-0.14, -1.2),
      (-0.02, -1.58), (0.25, -1.8), (0.52, -1.66), (0.54, -1.36), (0.34, -1.26), (0.26, -1.42)]
RAD = [0.2, 0.2, 0.3, 0.43, 0.41, 0.31, 0.23, 0.18, 0.14, 0.12, 0.1, 0.08, 0.06, 0.0]
def paint(p):
    if p.normal.x > 0.55 and p.center.y > -0.9: return "belly"
    return "band" if int((p.center.y + 3) / 0.2) % 2 == 0 else None
# more rings along the spine so the bony bands show
pts, rad = [], []
for i in range(len(SP) - 1):
    for k in range(2):
        t = k / 2
        pts.append((SP[i][0] + (SP[i + 1][0] - SP[i][0]) * t, SP[i][1] + (SP[i + 1][1] - SP[i][1]) * t, ZC))
        rad.append(RAD[i] + (RAD[i + 1] - RAD[i]) * t)
pts.append((*SP[-1], ZC)); rad.append(0.0)
tube(pts, rad, "body", sides=6, flat=0.8, paint=paint, name="body")
for i in range(1, 9):                                 # bony ridge down the back
    x, y = SP[i]
    cone((x - RAD[i] * 0.85, y, ZC), (x - RAD[i] - 0.14, y + 0.03, ZC), 0.07, "ridge", sides=4, name="ridge")
gem((0.14, 1.62, ZC), (0.3, 0.27, 0.24), "body", name="head")
tube([(0.34, 1.62, ZC), (0.66, 1.5, ZC), (0.95, 1.4, ZC)], [0.12, 0.085, 0.085], "body", sides=5, name="snout")
gem((0.98, 1.39, ZC), (0.11, 0.1, 0.11), "band", name="mouth")
for a, b in (((0.02, 1.84), (-0.02, 2.14)), ((0.2, 1.86), (0.3, 2.1)), ((-0.14, 1.74), (-0.36, 1.94))):
    cone((*a, ZC), (*b, ZC), 0.08, "ridge", sides=4, name="coronet")
for up in (1, -1):
    eye((0.22, 1.64, ZC + up * 0.2), 0.085, (0.15, 0, up))
# leaf fins: the back fin and a cheek fin, veined
plate([(-0.14, 0.75, ZC), (-0.62, 0.86, ZC), (-0.98, 0.5, ZC), (-0.9, 0.1, ZC), (-0.5, -0.12, ZC), (-0.12, 0.05, ZC)], 0.05, "leaf", name="back_fin")
for y0, y1 in ((0.62, 0.72), (0.4, 0.42), (0.18, 0.1)):
    tube([(-0.2, y0, ZC + 0.035), (-0.82, y1, ZC + 0.035)], [0.03, 0.0], "leaf2", sides=3, name="vein")
plate([(-0.12, 1.36, ZC + 0.12), (-0.5, 1.5, ZC + 0.16), (-0.52, 1.2, ZC + 0.16), (-0.2, 1.16, ZC + 0.12)], 0.04, "leaf", name="cheek_fin")
finish("gardener_seahorse", ASSETS + "/creature-gardener-seahorse")
