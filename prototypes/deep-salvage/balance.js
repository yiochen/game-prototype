export const BALANCE = Object.freeze({
  gridColumns: 6,
  gridRows: 5,
  storageSlots: 14,
  hull: 100,
  shield: 24,
  shieldDelay: 6,
  shieldRegen: 3,
  startingCash: 24,
  forgeSlots: 3,
  partDropEvery: 4,
  reactorPower: 8,
  amplifier: 1.5,
  powerCap: 48,
  laserDamagePerEnergy: 1.1,
  laserFeedbackInterval: 0.35,
  pulseCapacity: 36,
  pulseDamage: 54,
  pulseDuration: 0.3,
  lootLife: 12,
  lootFlash: 3,
  dragSpeed: 0.2,
  intermission: 7,
  submarine: { x: 0.23, y: 0.49 },
  floor: 0.86,
  enemies: {
    dart: { hp: 34, speed: 0.14, damage: 6, attackInterval: 1.2, armor: 0, bounty: 7 },
    bulwark: { hp: 300, speed: 0.038, damage: 15, attackInterval: 2.1, armor: 9, bounty: 24 },
    sniper: { hp: 95, speed: 0.055, damage: 10, attackInterval: 3, armor: 1, range: 0.6, bounty: 13 },
    leech: { hp: 100, speed: 0.08, damage: 8, attackInterval: 1.5, armor: 1, shieldDrain: 2, bounty: 12 },
    mender: { hp: 100, speed: 0.05, damage: 4, attackInterval: 2, armor: 0, healRate: 5, healRange: 0.22, bounty: 16 },
    bomber: { hp: 55, speed: 0.10, damage: 26, attackInterval: 0.8, armor: 0, suicide: true, bounty: 10 },
    scout: { hp: 38, speed: 0.065, damage: 7, attackInterval: 1.5, armor: 0, bounty: 8 },
    swarm: { hp: 20, speed: 0.115, damage: 5, attackInterval: 1.0, armor: 0, bounty: 5 },
    crab: { hp: 125, speed: 0.055, damage: 12, attackInterval: 1.8, armor: 4, bounty: 14 },
    warden: { hp: 180, shield: 40, speed: 0.06, damage: 14, attackInterval: 1.8, armor: 3, bounty: 18 },
  },
  waves: [
    { name: 'The sunken quarter', interval: 3.8, enemies: ['scout', 'scout', 'swarm', 'swarm', 'scout', 'crab', 'swarm', 'scout'] },
    { name: 'Through the kelp', interval: 1.9, enemies: ['scout', 'swarm', 'swarm', 'crab', 'scout', 'warden', 'swarm', 'swarm', 'crab', 'scout', 'warden', 'swarm', 'crab'] },
    { name: 'The outer beacon', interval: 1.0, enemies: ['warden', 'swarm', 'crab', 'swarm', 'scout', 'crab', 'swarm', 'warden', 'swarm', 'crab', 'scout', 'warden', 'swarm', 'crab', 'swarm', 'warden', 'crab', 'warden'] },
    { name: 'The flooded arcade', interval: 2.5, enemies: ['scout','crab','swarm','warden','scout','crab','swarm','warden','crab','swarm','scout','warden','crab','swarm'] },
    { name: 'Watchtower gauntlet', interval: 1.8, enemies: ['warden','crab','swarm','sniper','crab','scout','warden','swarm','bulwark','scout','crab','warden','swarm','sniper','crab','swarm','warden','crab'] },
    { name: 'The last beacon', interval: 1.4, enemies: ['warden','crab','swarm','bulwark','scout','warden','crab','swarm','sniper','crab','warden','swarm','bulwark','crab','scout','warden','sniper','swarm','crab','warden','crab','bulwark'] },
  ],
  lootOrder: ['splitter', 'lens', 'shield', 'splitter', 'pulse', 'medic', 'splitter', 'lens', 'reactor', 'amplifier'],
});

export const PART_RULES = Object.freeze({
  reactor: { power: BALANCE.reactorPower }, reactor2: { power: 12 },
  amplifier: { multiplier: BALANCE.amplifier }, amplifier2: { multiplier: 2.4 },
  mirror: { multiplier: 1 }, mirror2: { multiplier: 1.25 },
  splitter: { fraction: 0.5, forward: false },
  splitter2: { fraction: 0.5, forward: true },
  splitter3: { fraction: 1, forward: true },
  lens: { targets: 2, multiplier: 1 }, lens2: { targets: 3, multiplier: 1.25 },
  pulse: { multiplier: 1, capacity: BALANCE.pulseCapacity },
  shield: { multiplier: 1, capacity: 32, restore: 12, resource: 'shield' },
  shield2: { multiplier: 1, capacity: 32, restore: 20, resource: 'shield' },
  medic: { multiplier: 1, capacity: 48, restore: 12, resource: 'hull' },
  medic2: { multiplier: 1, capacity: 48, restore: 20, resource: 'hull' },
  gun: { multiplier: 1 }, gun2: { multiplier: 1.6 },
  prism: { multiplier: 1.75, targets: 2 },
  prism2: { multiplier: 2.8, targets: 2 },
});


export const ENEMY_INFO = Object.freeze({
  scout: { name: 'Scout', tactic: 'Steady all-round attacker. A continuous laser keeps it in check.', size: .155 },
  swarm: { name: 'Swarm', tactic: 'Small and fast. Multiple guns and piercing clear the pack.', size: .11 },
  crab: { name: 'Iron crab', tactic: 'Armored hull reduces non-piercing damage. Bring a lens.', size: .20 },
  warden: { name: 'Warden', tactic: 'Shielded heavy. Drain its shield, then pierce its armor.', size: .21 },
  dart: { name: 'Needle dart', tactic: 'The fastest attacker, with a fragile hull. Lasers avoid wasting a charged pulse.', size: .15 },
  bulwark: { name: 'Bulwark', tactic: 'Slow, thick armor and a huge hull. Piercing pulses work well.', size: .25 },
  sniper: { name: 'Harpoon sniper', tactic: 'Stops far away and fires every 3 seconds. Its aiming line warns of a shot.', size: .18 },
  leech: { name: 'Volt leech', tactic: 'Drains twice as much shield per hit. A Shield terminal replenishes protection during combat.', size: .17 },
  mender: { name: 'Reef mender', tactic: 'Repairs nearby allies for 5 HP per second, but cannot heal itself. Use piercing to reach it behind a tank.', size: .18 },
  bomber: { name: 'Depth bomber', tactic: 'Explodes for 26 damage on contact, then disappears. Destroy it before it reaches the submarine.', size: .16 },
});

export const MAPS = Object.freeze({
  city: { name: 'Sunken City', difficulty: 'Standard', theme: 'city', depth: 840, route: .025, top: 0x227893, bottom: 0x0f394c,
    description: 'Drowned streets and watchtowers. Learn to counter armored crabs and shielded wardens.', waves: BALANCE.waves },
  kelp: { name: 'Kelp Wilds', difficulty: 'Fast & relentless', theme: 'kelp', depth: 460, route: .065, top: 0x287f71, bottom: 0x123f47,
    description: 'A glowing forest. Darts rush ahead while leeches drain shields and menders repair the pack.', waves: [
      { name: 'Emerald shallows', interval: 3.6, enemies: ['scout','dart','swarm','leech','dart','mender','swarm','crab'] },
      { name: 'Tangled roots', interval: 1.7, enemies: ['dart','swarm','leech','mender','crab','dart','swarm','sniper','leech','dart','mender','swarm','crab'] },
      { name: 'The living reef', interval: 0.9, enemies: ['crab','dart','leech','mender','swarm','sniper','dart','leech','crab','mender','swarm','bomber','dart','warden','swarm','leech','mender','warden'] },
      { name: 'Quiet groves', interval: 2.5, enemies: ['dart','scout','leech','swarm','crab','dart','mender','scout','leech','swarm','crab','dart','warden','swarm'] },
      { name: 'Thorn passage', interval: 1.8, enemies: ['crab','leech','dart','mender','swarm','warden','dart','leech','crab','swarm','mender','dart','sniper','leech','swarm','warden','dart','crab'] },
      { name: 'Heart of the reef', interval: 1.4, enemies: ['warden','dart','leech','crab','swarm','mender','dart','bulwark','leech','swarm','crab','sniper','dart','warden','mender','swarm','leech','crab','dart','warden','leech','bulwark'] },
    ] },
  foundry: { name: 'Cinder Foundry', difficulty: 'Heavy fire', theme: 'foundry', depth: 1260, route: .045, top: 0x73596d, bottom: 0x272d46,
    description: 'Broken pipelines and volcanic vents. Snipers cover armored bulwarks and explosive drones.', waves: [
      { name: 'Cold pipelines', interval: 4, enemies: ['scout','bomber','scout','sniper','swarm','crab','bomber','scout'] },
      { name: 'Furnace channel', interval: 1.7, enemies: ['crab','sniper','bomber','swarm','bulwark','scout','bomber','leech','sniper','crab','swarm','mender','bomber'] },
      { name: 'The ember gate', interval: 1.0, enemies: ['bulwark','sniper','bomber','crab','swarm','mender','bomber','warden','sniper','leech','crab','bomber','bulwark','swarm','sniper','warden','bomber','bulwark'] },
      { name: 'Cooling reservoirs', interval: 2.6, enemies: ['scout','crab','bomber','swarm','sniper','scout','crab','swarm','warden','bomber','scout','crab','swarm','sniper'] },
      { name: 'Smelter crossing', interval: 1.9, enemies: ['bulwark','crab','bomber','swarm','sniper','warden','crab','scout','leech','bomber','crab','swarm','sniper','warden','bomber','crab','swarm','bulwark'] },
      { name: 'The furnace heart', interval: 1.5, enemies: ['bulwark','sniper','crab','swarm','bomber','warden','scout','crab','leech','bomber','sniper','bulwark','swarm','crab','warden','bomber','mender','crab','sniper','swarm','warden','bulwark'] },
    ] },
});
export const mapFor = state => MAPS[state.mapId] || MAPS.city;

// Consumable effects and loot cadence are independent of circuit rules.
export const CONSUMABLE_RULES = Object.freeze({
  repairKit: { resource: 'hull', amount: 25 },
  repairKit2: { resource: 'hull', amount: 60 },
  shieldCell: { resource: 'shield', amount: 12 },
  shieldCell2: { resource: 'shield', amount: 24 },
  timeCapsule: { seconds: 8 },
  timeCapsule2: { seconds: 20 },
});
export const CONSUMABLE_LOOT = Object.freeze({ earlyKill: 2, every: 6, order: ['repairKit', 'shieldCell', 'timeCapsule'] });
