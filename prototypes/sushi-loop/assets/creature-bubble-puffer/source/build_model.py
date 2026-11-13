"""Bubble Puffer (issue #66 concept, low-poly). Run in Blender with ASSETS set to this
assets folder: a round navy puffer with a cream belly, gold spikes and small fins.
It swims north (+Y); the tail points back at the ship."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("puffer", {
    "back": "#2c3f8f", "belly": "#f1e3c2", "fin": "#f2b632", "spike": "#f7cf52",
    "lip": "#e8a48c", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 1.05
R, H = 1.05, 0.92

# body: a fat ball, slightly longer than wide, with a short snout north
S = [-1.0, -0.86, -0.6, -0.25, 0.1, 0.45, 0.72, 0.9, 1.0]
W = [0.0, 0.52, 0.82, 0.98, 1.0, 0.90, 0.66, 0.36, 0.14]
loft([{"y": s * 1.12, "w": w * R, "h": w * H, "b": w * H * 0.9, "z": ZC} for s, w in zip(S, W)],
     "back", sides=12, name="body",
     paint=lambda p: "belly" if p.normal.z < 0.12 else None)
gem((0, 1.14, ZC - 0.02), (0.17, 0.09, 0.11), "lip", name="mouth")

# spikes: rings of short gold cones, standing off the skin
for lat, count, phase in ((62, 5, 0.0), (35, 9, 0.5), (8, 11, 0.0), (-20, 9, 0.5)):
    for k in range(count):
        a = 2 * math.pi * (k + phase) / count
        d = Vector((math.cos(math.radians(lat)) * math.sin(a), math.cos(math.radians(lat)) * math.cos(a), math.sin(math.radians(lat))))
        if d.y > 0.82: continue                       # keep the face clear
        base = Vector((d.x * R * 0.97, d.y * 1.05, ZC + d.z * H * 0.97))
        cone(base, base + d * 0.24, 0.085, "spike", sides=4)

for side in (-1, 1):
    eye((side * 0.56, 0.74, ZC + 0.42), 0.15, (side * 0.7, 0.35, 0.6))
    # pectoral fin: a small fan out of each flank
    plate([(side * 0.92, 0.30, ZC + 0.05), (side * 1.42, 0.42, ZC + 0.12), (side * 1.52, 0.12, ZC + 0.10),
           (side * 1.44, -0.16, ZC + 0.06), (side * 0.94, -0.02, ZC)], 0.05, "fin", name="pectoral")
# tail: stalk and fan, pointing south
loft([{"y": -1.0, "w": 0.2, "h": 0.2, "z": ZC}, {"y": -1.3, "w": 0.1, "h": 0.14, "z": ZC}], "back", sides=6, belly="belly", name="stalk")
plate([(0, -1.24, ZC), (0.34, -1.62, ZC), (0.16, -1.74, ZC), (0, -1.62, ZC), (-0.16, -1.74, ZC), (-0.34, -1.62, ZC)], 0.05, "fin", name="tail")
# dorsal fin, set back
plate([(0, -0.5, ZC + H * 0.84), (0, -0.78, ZC + H * 0.98), (0, -0.98, ZC + H * 0.66), (0, -0.86, ZC + H * 0.5)], 0.05, "fin", name="dorsal")

finish("bubble_puffer", ASSETS + "/creature-bubble-puffer")
