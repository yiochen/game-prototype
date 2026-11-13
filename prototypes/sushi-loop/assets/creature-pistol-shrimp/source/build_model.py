"""Pistol Shrimp (issue #72 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A stocky red shrimp with one oversized snapping claw (its right, +X),
held open ahead of it; the small left claw balances it."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("pistol", {
    "shell": "#c63a2c", "band": "#8f2118", "belly": "#f0b69a", "leg": "#de6a52",
    "claw": "#f39a2a", "finger": "#ffd27a", "fan": "#e0503a", "eye": "#141018",
})
ZC = 0.85
loft([{"y": 1.55, "w": 0.2, "h": 0.18, "z": ZC + 0.02}, {"y": 1.25, "w": 0.42, "h": 0.36, "z": ZC},
      {"y": 0.8, "w": 0.5, "h": 0.43, "z": ZC}, {"y": 0.3, "w": 0.48, "h": 0.41, "z": ZC}],
     "shell", sides=8, belly="belly", name="carapace",
     paint=lambda p: "band" if p.normal.z > 0.3 and 0.3 < p.center.y < 0.5 else None)
cone((0, 1.48, ZC + 0.1), (0, 1.95, ZC + 0.16), 0.07, "band", sides=4, name="rostrum")
segments(0.3, -1.35, 5, 0.48, 0.24, 0.41, 0.2, ZC, ZC - 0.18, "shell", "band", "belly")
plate([(0.13, -1.3, ZC - 0.18), (0, -1.85, ZC - 0.24), (-0.13, -1.3, ZC - 0.18)], 0.05, "band", name="telson")
for side in (-1, 1):
    for a, ln in ((24, 0.55), (56, 0.5)):
        d = Vector((side * math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
        n = Vector((-d.y, d.x, 0)) * 0.16
        o = Vector((side * 0.1, -1.32, ZC - 0.2))
        plate([o, o + d * ln * 0.55 + n, o + d * ln, o + d * ln * 0.55 - n], 0.04, "fan", name="uropod")
    gem((side * 0.26, 1.5, ZC + 0.13), 0.085, "eye", name="eye")
    tube([(side * 0.14, 1.55, ZC + 0.04), (side * 0.6, 2.2, ZC + 0.14), (side * 1.25, 1.9, ZC + 0.1), (side * 1.6, 0.7, ZC + 0.02), (side * 1.55, -0.3, ZC)],
         [0.04, 0.032, 0.026, 0.02, 0.0], "band", sides=3, name="antenna")
    for k in range(4):
        y = 1.0 - 0.24 * k
        tube([(side * 0.36, y, ZC - 0.26), (side * 0.9, y + 0.05, ZC - 0.4), (side * 1.05, y + 0.28, ZC - 0.74)], [0.055, 0.04, 0.0], "leg", sides=3, name="leg")
# the big snapping claw: arm, swollen palm, a fixed finger and the cocked-open thumb
tube([(0.4, 1.15, ZC - 0.08), (0.95, 1.45, ZC + 0.02), (1.15, 1.95, ZC + 0.05)], [0.14, 0.15, 0.17], "shell", sides=5, name="claw_arm")
gem((1.22, 2.45, ZC + 0.08), (0.46, 0.72, 0.36), "claw", name="claw_palm")
cone((1.05, 2.9, ZC + 0.06), (0.98, 3.85, ZC + 0.06), 0.22, "finger", sides=5, name="claw_finger")
cone((1.5, 2.85, ZC + 0.12), (1.95, 3.65, ZC + 0.16), 0.19, "finger", sides=5, name="claw_thumb")
gem((1.52, 2.8, ZC + 0.12), 0.17, "band", name="claw_hinge")
# the small claw
tube([(-0.4, 1.15, ZC - 0.08), (-0.85, 1.5, ZC), (-0.9, 1.95, ZC + 0.02)], [0.09, 0.09, 0.09], "shell", sides=4, name="small_arm")
gem((-0.92, 2.2, ZC + 0.03), (0.17, 0.3, 0.15), "claw", name="small_palm")
cone((-0.98, 2.4, ZC + 0.03), (-1.02, 2.85, ZC + 0.03), 0.08, "finger", sides=4, name="small_finger")
cone((-0.84, 2.4, ZC + 0.05), (-0.7, 2.8, ZC + 0.06), 0.07, "finger", sides=4, name="small_thumb")
finish("pistol_shrimp", ASSETS + "/creature-pistol-shrimp")
