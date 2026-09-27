// Original procedural scenery; this renderer contains no gameplay rules.
export function paintEnvironment(g, w, h, t, theme, wave) {
  if (theme === 'kelp') {
    for (let layer = 0; layer < 2; layer++) for (let i = 0; i < 11; i++) {
      const x = ((i * w * .15 - t * (layer ? 8 : 3)) % (w * 1.65) + w * 1.65) % (w * 1.65) - w * .12;
      const base = h * .97, height = h * (.35 + ((i * 3 + wave) % 7) * .09), sway = Math.sin(t * .7 + i) * 9;
      g.lineStyle(layer ? 7 : 11, layer ? 0x276f66 : 0x2e766f, layer ? .9 : .45);
      g.beginPath().moveTo(x, base).lineTo(x + sway, base - height * .5).lineTo(x - sway, base - height).strokePath();
      for (let leaf = 1; leaf < 7; leaf++) {
        const y = base - height * leaf / 7, side = leaf % 2 ? 1 : -1;
        g.fillStyle(layer ? 0x4aab86 : 0x428e7c, layer ? .6 : .3).fillEllipse(x + side * 12, y, 32, 12);
        if ((leaf + i + wave) % 4 === 0) g.fillStyle(0xc3efae, .65).fillCircle(x + side * 19, y, 2.5);
      }
    }
    for (let i = 0; i < 8; i++) {
      const x = (i * 69 + Math.sin(t * .4 + i) * 13) % w, y = h * (.18 + (i % 5) * .14);
      g.fillStyle(0x8eeac6, .10).fillCircle(x, y, 12);
      g.fillStyle(0xd0ffe1, .65).fillCircle(x, y, 2);
    }
  }
  if (theme === 'foundry') {
    for (let i = 0; i < 6; i++) {
      const x = ((i * w * .26 - t * 5) % (w * 1.56) + w * 1.56) % (w * 1.56) - w * .18;
      const top = h * (.25 + (i % 3) * .13);
      g.fillStyle(0x37374e, .85).fillRect(x, top, w * .12, h - top);
      g.lineStyle(12, 0x716178, .65).lineBetween(x + w * .06, top, x + w * .06, h);
      g.lineStyle(4, 0xa18a88, .5).lineBetween(x + w * .03, top, x + w * .03, h);
      for (let j = 0; j < 4; j++) g.fillStyle(0xb98468, .55).fillRect(x, top + j * 43, w * .12, 6);
      g.lineStyle(7, 0x574a61, .75).lineBetween(x - 20, top + 9, x + w * .3, top + 9);
      if ((i + wave) % 2 === 0) {
        g.fillStyle(0xf29a67, .08).fillEllipse(x, h * .91, 70, 150);
        g.fillStyle(0xde8355, .65).fillEllipse(x, h * .96, 32, 8);
        for (let j = 0; j < 6; j++) {
          const rise = (t * 24 + j * 24) % (h * .32);
          g.fillStyle(0xffbc75, .45 * (1 - rise / (h * .32))).fillCircle(x + Math.sin(j + t) * 9, h * .94 - rise, 3);
        }
      }
    }
  }
}
