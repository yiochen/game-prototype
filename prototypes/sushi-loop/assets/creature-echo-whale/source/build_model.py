"""Echo Whale (issue #80 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A humpback-like whale swimming north: navy back, pale belly, long
pale-edged flippers, a small dorsal hump and broad horizontal flukes."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("whale", {
    "back": "#27408b", "belly": "#e9eef8", "flipper": "#3b5bb5", "edge": "#dfe7f7",
    "knob": "#9fb4e6", "blow": "#131d44", "eye": "#f0d68c", "pupil": "#0b0f1e",
})
ZC = 1.2
Y = [3.0, 2.8, 2.3, 1.5, 0.6, -0.3, -1.1, -1.8, -2.35]
W = [0.0, 0.34, 0.62, 0.84, 0.9, 0.8, 0.56, 0.32, 0.15]
H = [0.0, 0.2, 0.42, 0.62, 0.7, 0.64, 0.48, 0.3, 0.15]
loft([{"y": y, "w": w, "h": h, "b": h * 0.9, "z": ZC} for y, w, h in zip(Y, W, H)], "back", sides=12, name="body",
     paint=lambda p: "belly" if p.normal.z < -0.1 else None)
gem((0, 1.95, ZC + 0.52), (0.1, 0.16, 0.05), "blow", name="blowhole")
for x, y in ((0, 2.75), (0.2, 2.5), (-0.2, 2.5), (0.36, 2.2), (-0.36, 2.2), (0, 2.35)):   # head knobs
    w, h = lerp_tab(-y, [-v for v in Y], W), lerp_tab(-y, [-v for v in Y], H)
    gem((x, y, ZC + h * math.sqrt(max(0, 1 - (x / w) ** 2))), 0.06, "knob", name="knob")
plate([(0, -0.7, ZC + 0.52), (0, -1.05, ZC + 0.78), (0, -1.4, ZC + 0.4)], 0.08, "back", name="dorsal")
plate([(0, -2.15, ZC), (0.5, -2.45, ZC), (1.35, -2.6, ZC), (1.5, -3.0, ZC), (0.7, -2.95, ZC), (0, -2.75, ZC),
       (-0.7, -2.95, ZC), (-1.5, -3.0, ZC), (-1.35, -2.6, ZC), (-0.5, -2.45, ZC)], 0.09, "back", name="flukes",
      paint=lambda p: "edge" if p.normal.z < -0.5 else None)
for side in (-1, 1):
    eye((side * 0.7, 1.9, ZC - 0.02), 0.07, (side, 0.1, 0.25))
    z = ZC - 0.22
    plate([(side * 0.78, 1.35, z), (side * 1.3, 1.2, z), (side * 2.2, 0.3, z - 0.05), (side * 2.5, -0.45, z - 0.1),
           (side * 2.15, -0.3, z - 0.1), (side * 1.4, 0.4, z - 0.03), (side * 0.8, 0.8, z)], 0.08, "flipper", name="flipper")
    strip([(side * 1.3, 1.2, z + 0.045), (side * 2.2, 0.3, z - 0.005), (side * 2.5, -0.45, z - 0.055)],
          [(side * 1.22, 1.08, z + 0.045), (side * 2.08, 0.2, z - 0.005), (side * 2.36, -0.4, z - 0.055)], 0.02, "edge", name="flipper_edge")
finish("echo_whale", ASSETS + "/creature-echo-whale")
