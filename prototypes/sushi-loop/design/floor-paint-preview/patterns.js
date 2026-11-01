// Review fixtures only. Cost and content are separate from interaction rules.
const cream = new URL('../expansion-preview/assets/floor-cream.png', import.meta.url).href;
const wave = new URL('../../assets/production/sprites/floor-blue-wave/static-S.png', import.meta.url).href;
const checker = new URL('../../assets/production/sprites/floor-checker/static-S.png', import.meta.url).href;
export const patterns = [
 {id:'blue-wave', name:'Blue Wave', image:wave, price:600},
 {id:'jade', name:'Jade Check', css:'jade', price:420},
 {id:'terracotta', name:'Terracotta', css:'terracotta', price:380},
 {id:'checker', name:'Harbor Check', image:checker, price:500},
 {id:'petal', name:'Plum Petal', css:'petal', price:650},
 {id:'linen', name:'Linen Stripe', css:'linen', price:240},
 {id:'cream', name:'Original Cream', image:cream, price:0},
];
export const patternById = id => patterns.find(p=>p.id===id)||patterns.at(-1);
export const initialOwned = patterns.slice(1).map(p=>p.id);
export const room = {columns:21, rows:13, backdropRows:3};
export const storageKey = 'sushi-loop-floor-ui-review-v1';
