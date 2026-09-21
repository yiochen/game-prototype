// All economy, offer weights, and effect strengths live here.
// Weights are relative within each category, not percentages after eligibility filtering.
// Arrays are TOTAL effects at levels 1, 2, 3, not increments to stack together.
export const BALANCE = {
  startingCash: 100,
  offerSize: 3,
  suits: [
    { id: 'bunny', name: 'Bunny', symbol: 'Bunny', color: '#d987a0' },
    { id: 'frog', name: 'Frog', symbol: 'Frog', color: '#8ea983' },
    { id: 'cat', name: 'Cat', symbol: 'Cat', color: '#d29b65' },
  ],
  families: { base: 55, growth: 20, reactor: 15, wealth: 10, strategy: 10 },
  base: {
    single: { name: 'One Room', price: 3, weight: 45, links: 1 },
    triple: { name: 'Prefab Pack', price: 6, weight: 35, links: 3 },
    choice: { name: 'Room Choice', price: 4, weight: 15, links: 1 },
    mosaic: { name: 'Mosaic', price: 6, weight: 20, patterns: [
      { id: 'trio', name: 'Trio', slots: [0, 1, 2] },
      { id: 'sandwich', name: 'Sandwich', slots: [0, 1, 0] },
      { id: 'pair-last', name: 'Pair', slots: [0, 1, 1] },
      { id: 'pair-first', name: 'Pair', slots: [0, 0, 1] },
    ] },
    mystery: { name: 'Surprise Parcel', price: 6, weight: 20, outcomes: [
      { links: 1, weight: 60 }, { links: 3, weight: 30 }, { links: 8, weight: 10 },
    ] },
  },
  growth: {
    recall: { name: 'Balloon Call', price: 7, weight: 80, linksPerSegment: 1 },
    overgrow: { name: 'Copycat', price: 5, weight: 20, linksPerBonus: 2, minimum: 1, maximum: 8 },
  },
  reactor: {
    suit: { name: 'Room Pattern', weight: 60, prices: [6, 8, 10], values: [1, 2, 3] },
    // Explicit distributions, equivalent to the old best-of-2 / 3 / 4 outcomes.
    // Change these weights directly to tune Stabilizer; Mystery makes one draw.
    stabilizer: { name: 'Lucky Bell', weight: 20, prices: [7, 9, 11], outcomesByLevel: [
      [{ links: 1, weight: 36 }, { links: 3, weight: 45 }, { links: 8, weight: 19 }],
      [{ links: 1, weight: 21.6 }, { links: 3, weight: 51.3 }, { links: 8, weight: 27.1 }],
      [{ links: 1, weight: 12.96 }, { links: 3, weight: 52.65 }, { links: 8, weight: 34.39 }],
    ] },
    assembler: { name: 'Master Fold', weight: 20, prices: [9, 12, 15], values: [1, 2, 3] },
  },
  wealth: {
    vault: { name: 'Reserve Delivery', price: 8, weight: 60, cashPerLink: 10, openingSuit: 'bunny' },
    rebate: { name: 'Coupon Book', price: 5, weight: 40, refund: 2, purchases: 3 },
  },
  strategy: {
    foundation: { name: 'Neighborhood Streak', price: 7, weight: 50, bonusStep: 1 },
    attunement: { name: 'Type Lock', price: 6, weight: 50, shops: 3 },
  },
};
