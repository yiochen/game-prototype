// Ingredient multisets: order never matters, but every copy and quantity does.
export const RECIPES = Object.freeze([
  { ingredients: ['shield', 'shield'], output: 'shield2', cost: 28, seconds: 7 },
  { ingredients: ['medic', 'medic'], output: 'medic2', cost: 32, seconds: 8 },
  { ingredients: ['gun', 'reactor'], output: 'pulse', cost: 24, seconds: 6 },
  { ingredients: ['reactor', 'reactor'], output: 'reactor2', cost: 30, seconds: 8 },
  { ingredients: ['mirror', 'mirror'], output: 'mirror2', cost: 16, seconds: 5 },
  { ingredients: ['amplifier', 'amplifier'], output: 'amplifier2', cost: 24, seconds: 6 },
  { ingredients: ['splitter', 'splitter'], output: 'splitter2', cost: 30, seconds: 7 },
  { ingredients: ['splitter2', 'splitter2'], output: 'splitter3', cost: 65, seconds: 10 },
  { ingredients: ['lens', 'lens'], output: 'lens2', cost: 28, seconds: 7 },
  { ingredients: ['gun', 'gun'], output: 'gun2', cost: 24, seconds: 6 },
  { ingredients: ['amplifier', 'lens'], output: 'prism', cost: 32, seconds: 8 },
  { ingredients: ['prism', 'amplifier2', 'lens2'], output: 'prism2', cost: 42, seconds: 9 },
  { ingredients: ['splitter2', 'mirror2', 'reactor2', 'gun2'], output: 'splitter3', cost: 60, seconds: 10 },
]);

// Match quantities against occupied forge slots; unrelated parts are ignored.
export function recipeSlots(recipe, slots) {
  const indices = [];
  for (const type of recipe.ingredients) {
    const index = slots.findIndex((part, i) => part?.type === type && !indices.includes(i));
    if (index < 0) return null;
    indices.push(index);
  }
  return indices;
}
