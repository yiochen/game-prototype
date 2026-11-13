"""Skipping Shrimp (issue #67 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A slender salmon shrimp: carapace and rostrum north, a plated abdomen
curving down to a fan tail at the south (the part that snaps), long antennae."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("shrimp", {
    "shell": "#f58a6b", "band": "#d9553f", "belly": "#ffd9c4", "leg": "#f7a98d",
    "fan": "#ff6f52", "tip": "#fff0e0", "eye": "#141018",
})
ZC = 0.85
loft([{"y": 1.82, "w": 0.16, "h": 0.15, "z": ZC + 0.03}, {"y": 1.5, "w": 0.33, "h": 0.30, "z": ZC},
      {"y": 1.0, "w": 0.41, "h": 0.38, "z": ZC}, {"y": 0.5, "w": 0.40, "h": 0.36, "z": ZC}],
     "shell", sides=8, belly="belly", name="carapace",
     paint=lambda p: "band" if p.normal.z > 0.3 and 0.5 < p.center.y < 0.72 else None)
cone((0, 1.7, ZC + 0.12), (0, 2.45, ZC + 0.24), 0.075, "band", sides=4, name="rostrum")
segments(0.5, -1.45, 6, 0.40, 0.19, 0.36, 0.17, ZC, ZC - 0.22, "shell", "band", "belly")
# fan tail: a pointed telson and two blades each side
plate([(0.1, -1.4, ZC - 0.22), (0, -2.05, ZC - 0.3), (-0.1, -1.4, ZC - 0.22)], 0.05, "band", name="telson")
for side in (-1, 1):
    for a, ln in ((22, 0.62), (52, 0.55)):
        d = Vector((side * math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
        n = Vector((-d.y, d.x, 0)) * 0.15
        o = Vector((side * 0.08, -1.42, ZC - 0.24))
        plate([o, o + d * ln * 0.55 + n, o + d * ln, o + d * ln * 0.55 - n], 0.04, "fan", name="uropod")
        plate([o + d * ln * 0.78 + n * 0.6, o + d * ln * 1.06, o + d * ln * 0.78 - n * 0.6], 0.045, "tip", name="uropod_tip")
    gem((side * 0.27, 1.72, ZC + 0.14), 0.095, "eye", name="eye")
    # long antenna sweeping out and back, and a short antennule ahead
    tube([(side * 0.14, 1.8, ZC + 0.05), (side * 0.55, 2.55, ZC + 0.18), (side * 1.05, 2.5, ZC + 0.14),
          (side * 1.45, 1.5, ZC + 0.06), (side * 1.62, 0.2, ZC), (side * 1.6, -0.9, ZC - 0.05)],
         [0.04, 0.035, 0.03, 0.025, 0.02, 0.0], "band", sides=3, name="antenna")
    tube([(side * 0.08, 1.85, ZC), (side * 0.22, 2.5, ZC + 0.05), (side * 0.3, 3.0, ZC + 0.02)], [0.03, 0.022, 0.0], "leg", sides=3, name="antennule")
    for k in range(5):            # walking legs under the carapace
        y = 1.45 - 0.2 * k
        tube([(side * 0.3, y, ZC - 0.25), (side * 0.78, y + 0.1, ZC - 0.4), (side * 0.92, y + 0.34, ZC - 0.72)], [0.045, 0.035, 0.0], "leg", sides=3, name="leg")
    for k in range(5):            # swimmerets under the abdomen
        y = 0.3 - 0.33 * k
        plate([(side * 0.2, y, ZC - 0.3 - 0.03 * k), (side * 0.48, y - 0.1, ZC - 0.52 - 0.03 * k), (side * 0.22, y - 0.2, ZC - 0.34 - 0.03 * k)], 0.03, "leg", name="swimmeret")
finish("skipping_shrimp", ASSETS + "/creature-skipping-shrimp")
