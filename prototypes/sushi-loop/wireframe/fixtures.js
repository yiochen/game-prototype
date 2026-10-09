// Authored review fixtures, never balance tables or a game simulation.
export const applicants = [
  { id: 'ama', name: 'Ama Mensah', role: 'Community caterer · Rotterdam', background: 'Ghanaian Dutch · practical, patient, community cook', trait: 'Fast grower', speed: '1.0×', growth: '+12% per level', growthRate: .12, ceiling: 8, tier: 'Silver', cost: 180, level: 1 },
  { id: 'mateo', name: 'Mateo Rivera', role: 'Bicycle mechanic · Oaxaca', background: 'Mexican · tinkerer and weekend market cook', trait: 'Low-cost hire', speed: '1.2×', growth: '+6% per level', growthRate: .06, ceiling: 5, tier: 'Copper', cost: 90, level: 1 },
  { id: 'noor', name: 'Noor Haddad', role: 'Botanical illustrator · Warsaw', background: 'Lebanese Polish · meticulous, curious home cook', trait: 'High ceiling', speed: '0.9×', growth: '+10% per level', growthRate: .10, ceiling: 12, tier: 'Gold', cost: 360, level: 1 },
];

export const startingChefs = [
  { id: 'lena', name: 'Lena Brooks', role: 'School-kitchen lead · Bristol', background: 'Black British · patient, practical, and happiest cooking for a crowd', level: 2, growthRate: .12, ceiling: 8, tier: 'Silver', trait: 'Reliable growth', assigned: true },
  { id: 'omar', name: 'Omar Haddad', role: 'Former bakery owner · Amman', background: 'Jordanian American · patient baker and weekend jazz listener', level: 1, growthRate: .08, ceiling: 12, tier: 'Gold', trait: 'Patient prep · high ceiling', assigned: false },
];

export const refreshedApplicants = [
  { id: 'dalia', name: 'Dalia Farouk', role: 'Paramedic · Montréal', background: 'Egyptian Canadian · calm under pressure and fond of family recipes', trait: 'Fast grower', speed: '1.0×', growth: '+12% per level', growthRate: .12, ceiling: 8, tier: 'Silver', cost: 180, level: 1 },
  { id: 'ellis', name: 'Ellis Morgan', role: 'Museum educator · Cardiff', background: 'White Welsh · storyteller and careful recipe collector', trait: 'Low-cost hire', speed: '1.2×', growth: '+6% per level', growthRate: .06, ceiling: 5, tier: 'Copper', cost: 90, level: 1 },
  { id: 'rowan', name: 'Rowan McLeod', role: 'Ferry deckhand · Glasgow', background: 'White Scottish · coastal gardener and adventurous cook', trait: 'High ceiling', speed: '0.9×', growth: '+10% per level', growthRate: .10, ceiling: 12, tier: 'Gold', cost: 360, level: 1 },
];

export const applicantSet = state => state.applicantRefresh ? refreshedApplicants : applicants;

export const chefAssigned = (state, chef) => !(state.unassignedChefs || []).includes(chef.id) && (chef.assigned || state.placedChef === chef.id);
export const chefSpeed = (chef, level) => ((parseFloat(chef.speed) || 1) + (level - 1) * chef.growthRate).toFixed(2);

export function roster(state) {
  return [...startingChefs, ...[...applicants, ...refreshedApplicants].filter(chef => (state.hiredApplicants || []).includes(chef.id))]
    .filter(chef => !(state.removedChefs || []).includes(chef.id));
}

export function chefFor(state) {
  return roster(state).find(chef => chef.id === state.selectedChef) || startingChefs[0];
}
