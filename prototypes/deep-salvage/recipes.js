// Unordered pairs; duplicate recipes consume two separate copies, not two drags
// of the same item. Costs and duration are deliberately independent of rules.
export const RECIPES = Object.freeze([
  { ingredients: ['reactor', 'reactor'], output: 'reactor2', cost: 30, seconds: 8 },
  { ingredients: ['mirror', 'mirror'], output: 'mirror2', cost: 16, seconds: 5 },
  { ingredients: ['amplifier', 'amplifier'], output: 'amplifier2', cost: 24, seconds: 6 },
  { ingredients: ['splitter', 'splitter'], output: 'splitter2', cost: 30, seconds: 7 },
  { ingredients: ['splitter2', 'splitter2'], output: 'splitter3', cost: 65, seconds: 10 },
  { ingredients: ['lens', 'lens'], output: 'lens2', cost: 28, seconds: 7 },
  { ingredients: ['gun', 'gun'], output: 'gun2', cost: 24, seconds: 6 },
  { ingredients: ['amplifier', 'lens'], output: 'prism', cost: 32, seconds: 8 },
]);

export function findRecipe(a, b) {
  return RECIPES.find(r => (r.ingredients[0] === a && r.ingredients[1] === b) || (r.ingredients[0] === b && r.ingredients[1] === a)) || null;
}

export function compatibleTypes(type) {
  return new Set(RECIPES.filter(r => r.ingredients.includes(type)).map(r => r.ingredients[0] === type ? r.ingredients[1] : r.ingredients[0]));
}
