"""Mason Crab (issue #79 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A wide red crab facing north: a faceted carapace, eyes on stalks, two
heavy boulder-grabbing claws held ahead and four jointed legs each side."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("crab", {
    "shell": "#d9482b", "dark": "#a52e1c", "belly": "#f3d9b0", "leg": "#e2603c",
    "claw": "#e8552f", "tip": "#f7e3c0", "eye": "#141018",
})
ZC = 0.75
Y = [0.85, 0.7, 0.4, 0.0, -0.4, -0.7, -0.82]
W = [0.5, 0.95, 1.25, 1.3, 1.1, 0.75, 0.4]
H = [0.12, 0.28, 0.4, 0.42, 0.36, 0.24, 0.1]
loft([{"y": y, "w": w, "h": h, "b": h * 0.7, "z": ZC} for y, w, h in zip(Y, W, H)], "shell", sides=12, name="carapace",
     paint=lambda p: "belly" if p.normal.z < -0.3 else ("dark" if p.normal.z > 0.9 and abs(p.center.x) < 0.7 else None))
for side in (-1, 1):
    for x in (0.55, 0.85):                            # knobs along the front edge
        cone((side * x, 0.68, ZC + 0.1), (side * (x + 0.06), 0.98, ZC + 0.14), 0.09, "dark", sides=4, name="knob")
    cone((side * 0.25, 0.8, ZC + 0.1), (side * 0.3, 0.98, ZC + 0.5), 0.06, "leg", sides=4, name="stalk")
    gem((side * 0.3, 0.99, ZC + 0.54), 0.1, "eye", name="eye")
    # claw arm, palm and two fingers, reaching ahead and inward
    tube([(side * 1.0, 0.55, ZC), (side * 1.65, 1.1, ZC + 0.12), (side * 1.4, 1.75, ZC + 0.18)], [0.2, 0.21, 0.2], "leg", sides=5, name="claw_arm")
    gem((side * 1.2, 2.15, ZC + 0.2), (0.44, 0.55, 0.34), "claw", name="claw_palm")
    cone((side * 1.38, 2.5, ZC + 0.2), (side * 1.12, 3.3, ZC + 0.2), 0.23, "tip", sides=5, name="claw_finger")
    cone((side * 0.98, 2.5, ZC + 0.24), (side * 0.66, 3.1, ZC + 0.26), 0.18, "tip", sides=5, name="claw_thumb")
    for k in range(4):                                # walking legs: hip, raised knee, pointed foot
        a = math.radians(25 - 32 * k)
        d = Vector((side * math.cos(a), math.sin(a), 0))
        hip = Vector((side * 1.0, 0.25 - 0.28 * k, ZC - 0.05))
        tube([hip, hip + d * 0.85 + Vector((0, 0, 0.42)), hip + d * 1.5 + Vector((0, -0.1, -0.1)), hip + d * 1.75 + Vector((0, -0.18, -0.62))],
             [0.13, 0.12, 0.09, 0.0], "leg", sides=4, name="leg", paint=lambda p: "dark" if p.center.z < 0.45 else None)
turn(Matrix.Scale(0.78, 4))                         # about 4.3 cells across the legs
finish("mason_crab", ASSETS + "/creature-mason-crab")
