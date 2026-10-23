// Verbatim pure consumer functions from world-sprite-raster.js SHA256 4ddc7495ade39f75adcce7d5400fc54326d588270b6fad9a5cca133f7df34bb0
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

export function paintWorldRaster(canvas, plan, loadedImages) {
  if (canvas.width !== plan.width) canvas.width = plan.width;
  if (canvas.height !== plan.height) canvas.height = plan.height;
  const context = canvas.getContext('2d');
  // Compose on the shared native grid before filtering the complete scene.
  // Filtering each fractional tile edge separately loses coverage at joins.
  context.imageSmoothingEnabled = false;
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (let index = 0; index < plan.sprites.length; index++) {
    const sprite = plan.sprites[index];
    context.drawImage(loadedImages[index], ...sprite.rect,
      (sprite.x - plan.x) * plan.scale, (sprite.y - plan.y) * plan.scale,
      sprite.width * plan.scale, sprite.height * plan.scale);
  }
}

