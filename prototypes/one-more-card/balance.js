// All economy, offer weights, and effect strengths live here.
// Weights are relative within each category, not percentages after eligibility filtering.
// Arrays are TOTAL effects at levels 1, 2, 3, not increments to stack together.
export const BALANCE = {
  startingCash: 100,
  offerSize: 3,
  suits: [
    { id: 'sun', name: 'Sun', symbol: '☀', color: '#f7ce78' },
    { id: 'moon', name: 'Moon', symbol: '☾', color: '#c7b4ff' },
    { id: 'wave', name: 'Wave', symbol: '≈', color: '#88dce8' },
  ],
  families: { base: 55, growth: 20, reactor: 15, wealth: 10, strategy: 10 },
  base: {
    single: { name: 'Fixed 1', price: 3, weight: 45, links: 1 },
    triple: { name: 'Fixed 3', price: 6, weight: 35, links: 3 },
    choice: { name: 'Choice 1', price: 4, weight: 15, links: 1 },
    mosaic: { name: 'Mosaic', price: 6, weight: 20, patterns: [
      { id: 'trio', name: 'Trio', slots: [0, 1, 2] },
      { id: 'sandwich', name: 'Sandwich', slots: [0, 1, 0] },
      { id: 'pair-last', name: 'Pair', slots: [0, 1, 1] },
      { id: 'pair-first', name: 'Pair', slots: [0, 0, 1] },
    ] },
    mystery: { name: 'Mystery', price: 6, weight: 20, outcomes: [
      { links: 1, weight: 60 }, { links: 3, weight: 30 }, { links: 8, weight: 10 },
    ] },
  },
  growth: {
    recall: { name: 'Recall', price: 7, weight: 80, linksPerSegment: 1 },
    overgrow: { name: 'Overgrow', price: 5, weight: 20, linksPerBonus: 2, minimum: 1, maximum: 8 },
  },
  reactor: {
    suit: { name: 'Reactor', weight: 60, prices: [6, 8, 10], values: [1, 2, 3] },
    // Explicit distributions, equivalent to the old best-of-2 / 3 / 4 outcomes.
    // Change these weights directly to tune Stabilizer; Mystery makes one draw.
    stabilizer: { name: 'Stabilizer', weight: 20, prices: [7, 9, 11], outcomesByLevel: [
      [{ links: 1, weight: 36 }, { links: 3, weight: 45 }, { links: 8, weight: 19 }],
      [{ links: 1, weight: 21.6 }, { links: 3, weight: 51.3 }, { links: 8, weight: 27.1 }],
      [{ links: 1, weight: 12.96 }, { links: 3, weight: 52.65 }, { links: 8, weight: 34.39 }],
    ] },
    assembler: { name: 'Assembler', weight: 20, prices: [9, 12, 15], values: [1, 2, 3] },
  },
  wealth: {
    vault: { name: 'Vault', price: 8, weight: 60, cashPerLink: 10, openingSuit: 'sun' },
    rebate: { name: 'Rebate', price: 5, weight: 40, refund: 2, purchases: 3 },
  },
  strategy: {
    foundation: { name: 'Foundation', price: 7, weight: 50, bonusStep: 1 },
    attunement: { name: 'Attunement', price: 6, weight: 50, shops: 3 },
  },
};
