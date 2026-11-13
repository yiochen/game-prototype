"""Pearl Oyster (issue #68 concept, low-poly). Run in Blender with ASSETS set to this
assets folder. Two ridged lavender shells hinged at the north, gaping south towards
the ship, with a soft pink body and a glowing pearl inside."""
exec(open(ASSETS + "/creature-kit/kit.py").read())
reset()
palette("oyster", {
    "shell": "#b9a2e6", "ridge": "#7f62c6", "inner": "#f1d9cf", "body": "#f6a9b8",
    "frill": "#e77f9a", "pearl": ("#fff4e6", "#ffe9c8", 0.5), "eye": "#3aa0d8", "hinge": "#6a52a8",
})
ZC = 0.95
HINGE_Y = 1.15
R, NA, NR, SPAN = 2.2, 14, 5, 1.2

def shell(sign, angle, dome):
    # an outer ridged sheet and a smooth inner one, joined round the lip
    m = Matrix.Translation((0, HINGE_Y, ZC)) @ Matrix.Rotation(math.radians(-sign * angle), 4, "X")
    def sheet(drop):
        bm = bmesh.new()
        grid = []
        for i in range(NA + 1):
            th = -SPAN + 2 * SPAN * i / NA
            row = []
            for j in range(NR + 1):
                t = 0.1 + 0.9 * j / NR
                r = R * t ** 0.9 * (1 + (0.06 if i % 2 == 0 else 0.0) * t) * (0.86 + 0.14 * math.cos(th))
                z = dome * (1 - (1 - t) ** 2) * (1 - 0.7 * t ** 4) * math.cos(th * 0.6) + (0.045 * t if i % 2 == 0 and not drop else 0)
                row.append(bm.verts.new(m @ Vector((r * math.sin(th), -r * math.cos(th), sign * (z - drop)))))
            grid.append(row)
        for i in range(NA):
            for j in range(NR):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        return bm, grid
    bm, grid = sheet(0.0)
    cols = {}
    for i in range(NA):
        for j in range(NR):
            c = (grid[i][j].co + grid[i + 1][j + 1].co) / 2
            cols[(round(c.x, 3), round(c.y, 3))] = i
    add(bm, "shell", lambda p: "ridge" if cols.get((round(p.center.x, 3), round(p.center.y, 3)), 1) % 2 == 0 else None, "shell_outer")
    bm, _ = sheet(0.09)
    add(bm, "inner", None, "shell_inner")

shell(1, 30, 0.55)
shell(-1, 5, 0.42)
gem((0, HINGE_Y - 0.02, ZC), (0.62, 0.2, 0.2), "hinge", name="hinge")
for side in (-1, 1):                                  # the hinge ears
    plate([(side * 0.3, HINGE_Y + 0.1, ZC), (side * 0.95, HINGE_Y + 0.12, ZC), (side * 0.7, HINGE_Y - 0.3, ZC)], 0.07, "ridge", name="ear")
# soft body, frilled mantle edge, and the pearl
gem((0, HINGE_Y - 1.0, ZC + 0.06), (1.0, 0.85, 0.2), "body", subdiv=2, name="body")
for k in range(9):
    a = -1.0 + 2.0 * k / 8
    gem((1.55 * math.sin(a), HINGE_Y - 1.6 * math.cos(a) * (0.86 + 0.14 * math.cos(a)), ZC + 0.02), (0.17, 0.13, 0.09), "frill", name="frill")
    if k % 2 == 0:                                     # a scallop's row of tiny eyes
        gem((1.62 * math.sin(a), HINGE_Y - 1.7 * math.cos(a) * (0.86 + 0.14 * math.cos(a)), ZC + 0.1), 0.05, "eye", name="eye")
gem((0, HINGE_Y - 1.45, ZC + 0.3), 0.36, "pearl", subdiv=2, name="pearl")
finish("pearl_oyster", ASSETS + "/creature-pearl-oyster")
