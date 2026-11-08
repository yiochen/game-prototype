// Cup geometry -> volume model for #62.
// Each cup is an interior profile: half width r(y) and centre offset dx(y), y measured up from the
// interior floor in px. Capacity per height is a circular cross-section, A(y) = pi * r(y)^2, so the
// same flow rises quickly through narrow sections and slowly through wide ones. The centre offset only
// shears the silhouette and never changes capacity; handles and feet are decoration outside the profile.

const STEP = 0.5;

const lerpPoints = (points, y) => {
  if (y <= points[0][0]) return points[0][1];
  for (let i = 1; i < points.length; i++) {
    const [y1, v1] = points[i];
    if (y <= y1) {
      const [y0, v0] = points[i - 1];
      // Smoothstep between control points so the silhouette has no kinks.
      const t = (y - y0) / (y1 - y0), s = t * t * (3 - 2 * t);
      return v0 + (v1 - v0) * s;
    }
  }
  return points[points.length - 1][1];
};

// Alternating round chambers joined by narrow throats.
function chambers(count, height, wide, narrow, neck) {
  const out = [];
  const each = height / count;
  for (let c = 0; c < count; c++) {
    for (let i = 0; i <= 8; i++) {
      const t = i / 8;
      if (c > 0 && i === 0) continue;
      out.push([c * each + t * each, narrow + (wide - narrow) * Math.sin(Math.PI * t) ** 0.8]);
    }
  }
  out.push([height + neck, narrow + 2]);
  return out;
}

export const CUP_DEFS = [
  {
    id: 'yunomi', name: 'Yunomi', note: 'Simple cup: an even rise',
    height: 132, target: 0.8, wall: 9, base: 12,
    radius: [[0, 30], [132, 35]],
    glaze: ['#f4e7cf', '#d8c3a0'], band: '#3a5c8c', foot: 6,
  },
  {
    id: 'bowl', name: 'Tea bowl', note: 'Narrow to wide: fast start, slow finish',
    height: 104, target: 0.82, wall: 8, base: 10,
    radius: [[0, 13], [30, 26], [70, 45], [104, 52]],
    glaze: ['#e7d6b8', '#b88d62'], band: '#7a4b2c', foot: 10,
  },
  {
    id: 'flask', name: 'Flask', note: 'Wide body, thin neck: delicate finish',
    height: 148, target: 0.84, wall: 8, base: 11,
    radius: [[0, 44], [54, 47], [84, 30], [104, 11], [148, 10]],
    glaze: ['#cfe1e8', '#7fa6b8'], band: '#2d4f77', foot: 0,
  },
  {
    id: 'hourglass', name: 'Hourglass', note: 'Wide, narrow waist, wide again',
    height: 148, target: 0.86, wall: 8, base: 10,
    radius: [[0, 40], [40, 38], [70, 9], [83, 9], [113, 38], [148, 42]],
    glaze: ['#f1d9d2', '#c98b7a'], band: '#8a3b2c', foot: 4,
  },
  {
    id: 'bubbles', name: 'Stacked bubbles', note: 'Chambers and throats: several speed changes',
    height: 150, target: 0.88, wall: 8, base: 10,
    radius: chambers(3, 134, 32, 8, 16),
    glaze: ['#e3ecd2', '#93ad74'], band: '#4b6a35', foot: 0,
  },
  {
    id: 'vase', name: 'Crooked vase', note: 'Uneven widths with an offset opening',
    height: 150, target: 0.84, wall: 8, base: 11,
    radius: [[0, 20], [31, 38], [64, 24], [95, 40], [128, 18], [150, 15]],
    shift: [[0, 0], [46, 12], [92, -10], [150, 22]],
    glaze: ['#ede3f0', '#a68bb4'], band: '#583b6c', foot: 3,
  },
];

export function makeCup(def) {
  const H = def.height;
  const n = Math.round(H / STEP);
  const rs = new Float64Array(n + 1), dxs = new Float64Array(n + 1), vol = new Float64Array(n + 1);
  for (let i = 0; i <= n; i++) {
    const y = i * STEP;
    rs[i] = lerpPoints(def.radius, y);
    dxs[i] = def.shift ? lerpPoints(def.shift, y) : 0;
    if (i) vol[i] = vol[i - 1] + Math.PI * ((rs[i - 1] + rs[i]) / 2) ** 2 * STEP;
  }
  const capacity = vol[n];
  const radiusAt = (y) => rs[Math.max(0, Math.min(n, Math.round(y / STEP)))];
  const shiftAt = (y) => dxs[Math.max(0, Math.min(n, Math.round(y / STEP)))];
  const volumeAt = (y) => {
    const f = Math.max(0, Math.min(n, y / STEP)), i = Math.floor(f);
    return i >= n ? capacity : vol[i] + (vol[i + 1] - vol[i]) * (f - i);
  };
  // Liquid height for a volume: binary search over the cumulative table.
  const levelFor = (v) => {
    if (v <= 0) return 0;
    if (v >= capacity) return H;
    let lo = 0, hi = n;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (vol[mid] < v) lo = mid; else hi = mid; }
    return (lo + (v - vol[lo]) / (vol[hi] - vol[lo])) * STEP;
  };
  const targetHeight = def.target * H;
  return {
    ...def, capacity, radiusAt, shiftAt, volumeAt, levelFor, targetHeight,
    targetVolume: volumeAt(targetHeight),
    // Rise speed (px of height per unit volume) at a height: 1 / A(y).
    riseRate: (y) => 1 / (Math.PI * radiusAt(y) ** 2),
    samples: () => Array.from({ length: n + 1 }, (_, i) => ({ y: i * STEP, r: rs[i], dx: dxs[i] })),
  };
}

export const CUPS = CUP_DEFS.map(makeCup);
