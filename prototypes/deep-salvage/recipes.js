// Ingredient multisets: order never matters, but every copy and quantity does.
export const RECIPES = Object.freeze([
  { ingredients: ['reactor', 'reactor'], output: 'reactor2', cost: 30, seconds: 8 },
  { ingredients: ['mirror', 'mirror'], output: 'mirror2', cost: 16, seconds: 5 },
  { ingredients: ['amplifier', 'amplifier'], output: 'amplifier2', cost: 24, seconds: 6 },
  { ingredients: ['splitter', 'splitter'], output: 'splitter2', cost: 30, seconds: 7 },
  { ingredients: ['splitter2', 'splitter2'], output: 'splitter3', cost: 65, seconds: 10 },
  { ingredients: ['lens', 'lens'], output: 'lens2', cost: 28, seconds: 7 },
  { ingredients: ['gun', 'gun'], output: 'gun2', cost: 24, seconds: 6 },
  { ingredients: ['amplifier', 'lens'], output: 'prism', cost: 32, seconds: 8 },
  { ingredients: ['amplifier', 'amplifier', 'lens'], output: 'prism2', cost: 42, seconds: 9 },
  { ingredients: ['splitter', 'splitter', 'splitter', 'splitter'], output: 'splitter3', cost: 60, seconds: 10 },
]);

export const recipeKey = ingredients => [...ingredients].sort().join('+');

export function findRecipe(...ingredients) {
  const key = recipeKey(ingredients);
  return RECIPES.find(r => recipeKey(r.ingredients) === key) || null;
}

// Suggest every remaining ingredient in recipes containing the current multiset.
export function compatibleTypes(ingredients) {
  const matches = new Set();
  if (!ingredients.length) return matches;
  for (const recipe of RECIPES) {
    const remaining = [...recipe.ingredients];
    let fits = true;
    for (const type of ingredients) {
      const index = remaining.indexOf(type);
      if (index < 0) { fits = false; break; }
      remaining.splice(index, 1);
    }
    if (fits) for (const type of remaining) matches.add(type);
  }
  return matches;
}
