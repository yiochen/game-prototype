import { segments } from './engine.js';

// Presentation time is independent of room construction and gameplay rules.
export const BALLOON_TIMING = Object.freeze({ bloom: 420, hover: 380, rise: 1680, stagger: 220 });
export const BALLOON_DURATION = BALLOON_TIMING.bloom + BALLOON_TIMING.hover + BALLOON_TIMING.rise;
const clamp = (n, min = 0, max = 1) => Math.max(min, Math.min(max, n));
const mix = (a, b, t) => a + (b - a) * t;
const smooth = t => t * t * (3 - 2 * t);
const cubic = (a, b, c, d, t) => (1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d;

export function balloonJourneys(before, after, roomsLandedAt) {
  return segments(after).filter(run => run.id >= before.nextLinkId).map((run, i) => ({
    ...run, side: i % 2 ? -1 : 1,
    startAt: roomsLandedAt + 120 + i * BALLOON_TIMING.stagger,
    arrived: false,
  }));
}

// source is the outer window of the new neighborhood's top floor. Recompute
// source and dock from live layout, so camera changes and resizes stay attached.
export function balloonPose(journey, elapsed, source, dock, size, viewportWidth) {
  const age = elapsed - journey.startAt;
  if (age < 0) return null;
  const { bloom, hover, rise } = BALLOON_TIMING, side = journey.side;
  const perch = { x: source.x + side * size * .42, y: source.y - size * .66 };
  let x, y, width, height, angle, alpha = 1, stage, travel = 0;
  if (age < bloom) {
    const t = clamp(age / bloom), open = 1 - (1 - t) ** 3;
    stage = 'emerging';
    x = mix(source.x, perch.x, open); y = mix(source.y - size * .1, perch.y, open);
    width = size * (.2 + .8 * open) * (1 - .06 * Math.sin(t * Math.PI));
    height = size * 1.28 * (.2 + .8 * open);
    angle = -side * 7 * open; alpha = clamp(t * 5);
  } else if (age < bloom + hover) {
    const t = (age - bloom) / hover;
    stage = 'hovering';
    x = perch.x + side * Math.sin(t * Math.PI) * 3;
    y = perch.y - Math.sin(t * Math.PI) * 5;
    width = size; height = size * 1.28; angle = -side * 7 * (1 - smooth(t));
  } else {
    travel = clamp((age - bloom - hover) / rise);
    const t = smooth(travel), lift = Math.max(0, perch.y - dock.y);
    const breeze = Math.min(66, Math.abs(dock.x - perch.x) * .16 + 28);
    stage = travel === 1 ? 'arrived' : travel > .84 ? 'docking' : 'rising';
    x = cubic(perch.x, perch.x + side * breeze, dock.x + side * 24, dock.x, t);
    x += Math.sin(travel * Math.PI * 3) * Math.sin(travel * Math.PI) * 5;
    y = cubic(perch.y, perch.y - lift * .35, dock.y + lift * .16, dock.y, t);
    width = mix(size, dock.width, t); height = mix(size * 1.28, dock.height, t);
    angle = Math.sin(travel * Math.PI * 2) * Math.sin(travel * Math.PI) * 7;
    alpha = 1 - smooth(clamp((travel - .88) / .12));
  }
  return { x: clamp(x, width / 2 + 6, viewportWidth - width / 2 - 6), y, width, height, angle, alpha, stage, travel };
}
