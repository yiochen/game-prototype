export function worldRasterPlan(sprites, bounds) {
  const scale = Math.max(1, ...sprites.map(sprite => Math.max(sprite.rect[2] / sprite.width, sprite.rect[3] / sprite.height)));
  // Anchor to the authored world pixel grid, never to a fractional camera pan.
  // One guard pixel lets the browser filter the outer viewport edge normally.
  const x = (Math.floor(bounds[0] * scale) - 1) / scale;
  const y = (Math.floor(bounds[1] * scale) - 1) / scale;
  const width = Math.ceil((bounds[0] + bounds[2] - x) * scale) + 1;
  const height = Math.ceil((bounds[1] + bounds[3] - y) * scale) + 1;
  return { x, y, width, height, scale, sprites };
}

const rasterLayers = new WeakMap();

export function paintWorldRaster(canvas, plan, loadedImages) {
  if (canvas.width !== plan.width) canvas.width = plan.width;
  if (canvas.height !== plan.height) canvas.height = plan.height;
  const context = canvas.getContext('2d');
  // Compose on the shared native grid before filtering the complete scene.
  // Filtering each fractional tile edge separately loses coverage at joins.
  context.imageSmoothingEnabled = false;
  context.clearRect(0, 0, canvas.width, canvas.height);
  const position = sprite => [(sprite.x - plan.x) * plan.scale, (sprite.y - plan.y) * plan.scale];
  const integral = value => Math.abs(value - Math.round(value)) <= Number.EPSILON * Math.max(1, Math.abs(value)) * 8;
  for (let index = 0; index < plan.sprites.length;) {
    const sprite = plan.sprites[index];
    const [x, y] = position(sprite);
    const width = sprite.width * plan.scale, height = sprite.height * plan.scale;
    const group = [{ index, x: 0, y: 0, width, height }];
    let end = index + 1, left = 0, top = 0, right = width, bottom = height;
    if (integral(width) && integral(height)) {
      while (end < plan.sprites.length) {
        const next = plan.sprites[end], [nextX, nextY] = position(next);
        const dx = nextX - x, dy = nextY - y;
        const nextWidth = next.width * plan.scale, nextHeight = next.height * plan.scale;
        if (![dx, dy, nextWidth, nextHeight].every(integral)) break;
        const gx = Math.round(dx), gy = Math.round(dy);
        group.push({ index: end, x: gx, y: gy, width: Math.round(nextWidth), height: Math.round(nextHeight) });
        left = Math.min(left, gx); top = Math.min(top, gy);
        right = Math.max(right, gx + Math.round(nextWidth)); bottom = Math.max(bottom, gy + Math.round(nextHeight));
        end++;
      }
    }
    if (group.length === 1 || (integral(x) && integral(y))) {
      for (const item of group) {
        const current = plan.sprites[item.index], [dx, dy] = position(current);
        context.drawImage(loadedImages[item.index], ...current.rect,
          dx, dy, current.width * plan.scale, current.height * plan.scale);
      }
    } else {
      // Chrome can antialias a fractional drawImage boundary even with nearest
      // sampling. Compose consecutive tiles sharing a native pixel phase at
      // integer offsets first, then translate the complete layer once. This
      // retains their original positions and painter order without tile overlap.
      let layer = rasterLayers.get(canvas);
      if (!layer) { layer = canvas.ownerDocument.createElement('canvas'); rasterLayers.set(canvas, layer); }
      if (layer.width !== right - left) layer.width = right - left;
      if (layer.height !== bottom - top) layer.height = bottom - top;
      const layerContext = layer.getContext('2d');
      layerContext.imageSmoothingEnabled = false;
      layerContext.clearRect(0, 0, layer.width, layer.height);
      for (const item of group) layerContext.drawImage(loadedImages[item.index],
        ...plan.sprites[item.index].rect, item.x - left, item.y - top, item.width, item.height);
      context.drawImage(layer, x + left, y + top);
    }
    index = end;
  }
}

