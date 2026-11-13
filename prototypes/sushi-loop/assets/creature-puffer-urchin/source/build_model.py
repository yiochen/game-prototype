"""Puffer Urchin (issue #78 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. A purple sea urchin: a faceted ball bristling with pale-tipped spines,
with five glowing pink plates on its crown (the pulse the engine can drive)."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("urchin", {
    "body": "#4a1f7a", "spine": "#6c2fb0", "tip": "#e7b8ff", "glow": ("#ff9be6", "#ff6fd8", 2.0), "under": "#2e1250",
})
ZC = 1.15
R, H = 0.82, 0.74
gem((0, 0, ZC), (R, R, H), "body", subdiv=2, name="test", paint=lambda p: "under" if p.normal.z < -0.5 else None)
N = 64
for i in range(N):                                    # an even spread of spines
    z = 1 - 2 * (i + 0.5) / N
    if z < -0.55: continue
    rr = math.sqrt(1 - z * z); a = i * math.pi * (3 - math.sqrt(5))
    d = Vector((rr * math.cos(a), rr * math.sin(a), z))
    base = Vector((d.x * R * 0.93, d.y * R * 0.93, ZC + d.z * H * 0.93))
    ln = 0.78 + 0.12 * math.sin(i * 1.7)
    cone(base, base + d * ln, 0.1, "spine", sides=4, name="spine")
    cone(base + d * ln * 0.62, base + d * (ln + 0.06), 0.052, "tip", sides=4, name="spine_tip")
for k in range(5):                                    # five-fold plates round the crown
    a = 2 * math.pi * k / 5
    gem((0.34 * math.sin(a), 0.34 * math.cos(a), ZC + H * 0.93), (0.1, 0.1, 0.04), "glow", name="plate")
finish("puffer_urchin", ASSETS + "/creature-puffer-urchin")
