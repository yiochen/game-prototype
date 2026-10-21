// Projected wall-plane dimensions: no additional environment-height multiplier.
export const backdropGeometry = Object.freeze({ rows: 3, gateWidth: 4, openingWidth: 2, leftWallWidth: 3 });

export function backdropLayout(columns = 7, decorated = false) {
  const { rows, gateWidth, openingWidth, leftWallWidth } = backdropGeometry;
  const gateX = leftWallWidth;
  return {
    walls: Array.from({ length: columns }, (_, x) => x).filter(x => x < gateX || x >= gateX + gateWidth).map(x => ({ id: `wall-${x}`, asset: decorated && x % 3 === 0 ? 'wall-window' : 'wall-plain', x, y: 0, width: 1, height: rows })),
    gate: { id: 'gate', asset: 'gate', x: gateX, y: 0, width: gateWidth, height: rows },
    opening: { x: gateX + (gateWidth - openingWidth) / 2, width: openingWidth },
  };
}
