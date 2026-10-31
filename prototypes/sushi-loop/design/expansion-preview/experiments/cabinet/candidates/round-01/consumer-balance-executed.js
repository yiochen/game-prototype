// Prototype review content; native integration follows approval.
export const floor={columns:21,rows:13,starterColumns:7,backdropRows:3};
export const economy={startingCoins:120,reviewCoins:640,saleCoins:14,saleSeconds:8};
export const dockCells=Array.from({length:9},(_,i)=>[7+i%3,6+Math.floor(i/3)]);
export const trashFamilies=[
 {id:'garbage-sofa',name:'Broken sofa',footprint:[2,2],price:120},
 {id:'garbage-car',name:'Wrecked car',footprint:[3,2],price:180},
 {id:'garbage-shelving',name:'Collapsed shelving',footprint:[2,2],price:140},
 {id:'garbage-armchair',name:'Broken armchair',footprint:[1,1],price:45},
 {id:'garbage-cabinet',name:'Broken cabinet',footprint:[2,1],price:90},
];
const family=id=>trashFamilies.find(f=>f.id===id);
const make=(id,type,x,y,facing='S',extra={})=>{const f=family(type),rotated=['E','W'].includes(facing);return {id,name:f.name,family:type,art:`${type}-${facing}`,facing,x,y,w:f.footprint[rotated?1:0],h:f.footprint[rotated?0:1],price:f.price,...extra};};
// Dock is separately covered. No trash sprite owns an invisible surrounding region.
const occupied=new Set(dockCells.map(c=>c.join(',')));
const list=[];
function add(p){for(let y=p.y;y<p.y+p.h;y++)for(let x=p.x;x<p.x+p.w;x++){if(occupied.has(`${x},${y}`))throw new Error('Overlapping content footprint '+p.id);occupied.add(`${x},${y}`);}list.push(p);}
add(make('sofa-west','garbage-sofa',7,3));
add(make('cabinet-west','garbage-cabinet',9,3));
add(make('armchair-west','garbage-armchair',7,5));
add(make('dock-access','garbage-car',7,9,'S',{access:true}));
add(make('shelves-west','garbage-shelving',7,11));
// A fixed seed creates a reproducible, predefined packing. Different families,
// sizes and native facings break the repeated sofa/car/shelf rows from v1.
let seed=191029;
const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
const fits=p=>p.x+p.w<=floor.columns&&p.y+p.h<=floor.rows&&Array.from({length:p.h},(_,dy)=>Array.from({length:p.w},(_,dx)=>!occupied.has(`${p.x+dx},${p.y+dy}`)).every(Boolean)).every(Boolean);
for(let y=3;y<13;y++)for(let x=7;x<21;x++){
 if(occupied.has(`${x},${y}`))continue;
 const directions=['S','W','N','E'];
 const choices=trashFamilies.flatMap(f=>directions.map(d=>make(`trash-${x}-${y}`,f.id,x,y,d))).filter(fits);
 const nearby=list.filter(p=>Math.abs(p.x-x)+Math.abs(p.y-y)<4).map(p=>p.family);
 const scores=choices.map(p=>({p,score:random()+p.w*p.h*.12-nearby.filter(f=>f===p.family).length*.24})).sort((a,b)=>b.score-a.score);
 add(scores[0].p);
}
export const patches=Object.freeze(list);
// Actual outer edges only. All props keep original uniform scale; staggered
// roots and native facings form uneven clusters instead of periodic bundles.
const decor=(id,art,x,y,facing='S',layer=0)=>({id,art:`${art}-${facing}`,family:art,x,y,layer});
const leftRocks=Array.from({length:17},(_,i)=>decor(`left-bed-${i}`,'slate-rock',[-.64,-1.12,-.86][i%3],2.8+i*.66,['E','S','W','N'][((i*7)%5)%4],-8));
const leftDetails=[
 ['plant-angular',-.66,3.25,'E'],['plant-angular',-1.15,3.72,'N'],['crate-wood',-.64,4.15,'W'],
 ['plant-angular',-.67,4.9,'W'],['lantern-gold',-.66,5.55,'S'],['plant-angular',-1.08,5.9,'N'],
 ['barrel-wood',-.65,6.6,'E'],['plant-angular',-1.05,7.1,'W'],['plant-angular',-.67,7.75,'S'],
 ['crate-wood',-.66,8.3,'S'],['plant-angular',-.7,8.85,'E'],['sign-blank',-.67,9.45,'S'],
 ['plant-angular',-1.04,9.8,'S'],['lantern-gold',-.7,10.15,'S'],['plant-angular',-.67,10.8,'N'],
 ['crate-wood',-1.12,11.35,'E'],['plant-angular',-.65,11.7,'W'],['barrel-wood',-.67,12.3,'W'],
 ['plant-angular',-1.1,12.75,'E'],['plant-angular',-.64,13.25,'S'],['crate-wood',-.6,13.85,'S'],
].map(([art,x,y,d],i)=>decor(`left-accent-${i}`,art,x,y,d));
const right=Array.from({length:16},(_,i)=>decor(`right-${i}`,['plant-angular','slate-rock','crate-wood','plant-angular','barrel-wood','slate-rock','lantern-gold'][i%7],21.65+(i%3===0?.4:0),3.1+i*.68,['W','N','S','E'][i%4]));
const bottom=Array.from({length:25},(_,i)=>decor(`bottom-${i}`,['slate-rock','plant-angular','crate-wood','slate-rock','plant-angular','barrel-wood','lantern-gold','plant-angular'][i%8],-.7+i*.94,13.65+(i%3)*.2,['E','N','W','S'][i%4]));
export const decorations=[...leftRocks,...leftDetails,...right,...bottom];

