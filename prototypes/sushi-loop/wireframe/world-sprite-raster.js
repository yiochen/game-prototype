import { useLayoutEffect, useRef, useState } from 'react';

const images = new Map();

function spriteImage(url) {
  let entry = images.get(url);
  if (entry) {
    images.delete(url);
    images.set(url, entry);
    return entry;
  }
  const image = new Image();
  entry = { image, loaded: false };
  entry.promise = new Promise((resolve, reject) => {
    image.onload = () => { entry.loaded = true; resolve(image); };
    image.onerror = () => { images.delete(url); reject(new Error(`Sprite failed to load: ${url}`)); };
  });
  image.src = url;
  images.set(url, entry);
  // Review pages mount many different studies over time. Keep the active scene
  // hot without retaining every decoded atlas visited during a catalog review.
  if (images.size > 128) images.delete(images.keys().next().value);
  return entry;
}

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

export function useWorldSpriteRaster(sprites, bounds) {
  const canvas = useRef(null);
  const plan = worldRasterPlan(sprites, bounds);
  const signature = JSON.stringify(plan);
  const [readySignature, setReadySignature] = useState(null);
  const [error, setError] = useState(null);
  useLayoutEffect(() => {
    let cancelled = false;
    const current = JSON.parse(signature);
    const entries = current.sprites.map(sprite => spriteImage(sprite.url));
    const paint = loaded => {
      if (cancelled || !canvas.current) return;
      paintWorldRaster(canvas.current, current, loaded);
      setError(null);
      setReadySignature(signature);
    };
    if (entries.every(entry => entry.loaded)) paint(entries.map(entry => entry.image));
    else Promise.all(entries.map(entry => entry.promise)).then(paint, failure => {
      if (!cancelled) { setError(failure.message); setReadySignature(null); }
    });
    return () => { cancelled = true; };
  }, [signature]);
  return { canvas, plan, ready: readySignature === signature, error };
}
