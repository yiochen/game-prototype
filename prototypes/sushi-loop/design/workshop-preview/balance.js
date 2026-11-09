// Review fixtures for #28. Tune equipment here; rules live in model.js.
// `levels[i]` is the stat at level i+1; `costs[i]` buys level i+2.
// `looks` are the levels at which that part's sprite is replaced by the next tier (appearance milestones);
// `tiers` name the three looks: base, first milestone, maximum.
export const tracks = [
  {id: 'hull', name: 'Hull', stat: 'Maximum hull', tiers: ['Starter hull', 'Reinforced hull', 'Deep-sea hull'],
   levels: [100, 125, 150, 175, 200], costs: [60, 110, 170, 240], looks: [3, 5],
   format: v => String(v)},
  {id: 'harpoon', name: 'Harpoon', stat: 'Reeling strength', tiers: ['Starter harpoon', 'Reel harpoon', 'Storm harpoon'],
   levels: [1, 1.2, 1.4, 1.6, 1.8], costs: [70, 120, 180, 260], looks: [3, 5],
   format: v => `${v.toFixed(1)}×`},
  // Modest cap: attraction never passes 1.5 tiles and never multiplies pickup value.
  {id: 'collector', name: 'Collector', stat: 'Attraction range', tiers: ['Net scoops', 'Fan intakes', 'Magnet coils'],
   levels: [0.6, 0.9, 1.2, 1.5], costs: [50, 95, 150], looks: [3, 4],
   format: v => `${(v / 0.6).toFixed(1)}×`}, // shown relative to the base reach; tiles are internal
  // Power-ups (r5): upgrades to the expedition pickups. Their looks are a colour change of the effect
  // (see tierColors), not a ship part. Shields still end before the creature encounter.
  {id: 'shield', group: 'powerup', name: 'Shield', does: 'Shield pickups block rock hits', better: 'Lasts longer', tiers: ['White shield', 'Violet shield', 'Gold shield'],
   levels: [3.5, 4.25, 5, 5.75, 6.5], costs: [80, 130, 190, 260], looks: [3, 5],
   format: v => String(+v.toFixed(2))},
  {id: 'passage', group: 'powerup', name: 'Passage', does: 'Portals carry you through a salvage current', better: 'Longer ride', tiers: ['White current', 'Violet current', 'Gold current'],
   levels: [28, 34, 40, 46], costs: [90, 150, 230], looks: [3, 4],
   format: v => String(v)},
  // Shield at start: launch already shielded. Level 1 is none; it uses the Shield track's colour.
  {id: 'launch', group: 'powerup', name: 'Shield at start', does: 'Begin each dive already shielded', better: 'Lasts longer', unlock: 'Unlock', tiers: ['None', 'Short', 'Long'],
   levels: [0, 1.5, 2.5, 3.5], costs: [100, 170, 260], looks: [2, 4],
   format: v => v ? v.toFixed(1) : 'None'},
];
for (const t of tracks) t.group ??= 'equipment';
export const groups = [{id: 'equipment', name: 'Equipment'}, {id: 'powerup', name: 'Power-ups'}];
// Power-up look tiers are colours: white (native), violet, gold — all clear on the cyan water.
export const tierColors = ['#e8fdff', '#c39bff', '#ffd552'];
// Interaction signal in the dive (r5 glow test): lime for good/interactable, red reserved for harmful.
export const signal = {good: '#b4ff2e', bad: '#ff3b3b'};

// Native expedition values the dive comparison reads (godot/content/expedition.json).
export const expedition = {impactDamage: 25, resistance: 100, resistanceDrainPerSecond: 4.5, shipRadius: 0.3, salvagePerPickup: 2, shieldSeconds: 3.5, passageRows: 28};

export const fixtures = {
  workshop: {salvage: 420, levels: {hull: 2, harpoon: 1, collector: 1, shield: 1, passage: 1, launch: 1}},
  unaffordable: {salvage: 25, levels: {hull: 2, harpoon: 1, collector: 1, shield: 1, passage: 1, launch: 1}},
  max: {salvage: 320, levels: {hull: 5, harpoon: 3, collector: 4, shield: 5, passage: 2, launch: 4}},
  restaurant: {salvage: 420, levels: {hull: 2, harpoon: 1, collector: 1, shield: 1, passage: 1, launch: 1}},
  dive: {salvage: 180, levels: {hull: 3, harpoon: 3, collector: 3, shield: 3, passage: 3, launch: 2}},
  edit: {salvage: 420, levels: {hull: 2, harpoon: 1, collector: 1, shield: 1, passage: 1, launch: 1}},
  gallery: {salvage: 180, levels: {hull: 2, harpoon: 1, collector: 1, shield: 1, passage: 1, launch: 1}},
};

// Live service keeps earning while the Workshop is open (review clock only).
export const live = {cash: 9180, saleEverySeconds: 2.6, saleAmounts: [12, 18, 24, 9]};
