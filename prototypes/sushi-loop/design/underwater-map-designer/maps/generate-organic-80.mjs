import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {parseMap,exportMap,paintCells} from '../model.js';
const source=new URL('./sources/turquoise-passage-user-reference.json',import.meta.url);
const raw=readFileSync(source,'utf8'),reference=parseMap(raw);
// Progress rows ascend from the bottom. Preserve the user's entire first 25 rows.
const opening=reference.placements.filter(p=>p.y>=55);
// Deliberately authored coast profiles; '.' is navigable water, '#' is an obstacle.
// Width changes create turn shoulders rather than alternating rectangular gates.
const extension=[
 /*26*/ '#....##', '#...###', '#..####', '#..####', '#...###',
 /*31*/ '##...##', '###..##', '###..##', '##....#', '#.....#',
 /*36*/ '#..#...', '#..#...', '#..#..#', '#.....#', '##....#',
 /*41*/ '###...#', '####..#', '####..#', '###...#', '##...##',
 /*46*/ '##..###', '##..###', '#...###', '#....##', '##....#',
 /*51*/ '###...#', '####..#', '####..#', '###...#', '##...##',
 /*56*/ '##..###', '##..###', '##...##', '###...#', '####..#',
 /*61*/ '###...#', '##....#', '##...##', '##..###', '##..###',
 /*66*/ '##...##', '###...#', '###...#', '#....##', '#...###',
 /*71*/ '#..####', '#..####', '#...###', '##...##', '###..##',
 /*76*/ '###..##', '###...#', '#.....#', '......#', '.......',
];
if(extension.length!==55||extension.some(s=>s.length!==7))throw Error('Expected 55 seven-cell coast profiles.');
const obstacle=new Set();
for(const p of opening)if(p.layer==='obstacles')obstacle.add(`${p.x}:${80-p.y}`);
for(let i=0;i<extension.length;i++)for(let x=0;x<7;x++)if(extension[i][x]==='#')obstacle.add(`${x}:${i+26}`);
const blocked=(x,r)=>x<0||x>=7||r<1||r>80||obstacle.has(`${x}:${r}`);
// A reproducible hash gives clustered, non-striped scenery without random build drift.
const noise=(x,r,salt=0)=>{let h=Math.imul(x+31,374761393)^Math.imul(r+17,668265263)^Math.imul(salt+11,1274126177);h=Math.imul(h^(h>>>13),1274126177);return ((h^(h>>>16))>>>0)/4294967296;};
const cells=[];
for(let r=26;r<=80;r++)for(let x=0;x<7;x++)if(blocked(x,r))cells.push({layer:'obstacles',object:'rock-wall-middle',x,y:80-r,direction:'S'});
const decor=new Set();
for(let r=26;r<=80;r++)for(let x=0;x<7;x++){
 const key=`${x}:${r}`;
 if(blocked(x,r)){
  const exposed=[[-1,0],[1,0],[0,-1],[0,1]].some(([dx,dr])=>!blocked(x+dx,r+dr));
  // Place foliage on the surfaces that frame the passage, with irregular bare rock relief.
  if((exposed&&noise(Math.floor(x/2),Math.floor(r/2),1)<.91)||(!exposed&&noise(x,Math.floor(r/3),2)<.48))decor.add(key);
 }else{
  const near=[[-1,0],[1,0],[0,-1],[0,1]].filter(([dx,dr])=>x+dx>=0&&x+dx<7&&r+dr>=26&&r+dr<=80&&blocked(x+dx,r+dr)).length;
  // Fringe the wider bays, but keep the narrow two-cell passages visually clear.
  const free=Array.from({length:7},(_,i)=>i).filter(i=>!blocked(i,r));
  const edgeOfBay=(x===free[0]||x===free.at(-1))&&free.length>=3;
  if(near>0&&edgeOfBay&&noise(x,Math.floor(r/2),3)<.58)decor.add(key);
 }
}
// Every obstacle cell is dressed directly or accompanied by foliage on a neighboring
// obstacle. This avoids lonely bare clusters without filling the traversable route.
for(let r=26;r<=80;r++)for(let x=0;x<7;x++)if(blocked(x,r)){
 if(![[-1,0],[1,0],[0,-1],[0,1],[0,0]].some(([dx,dr])=>decor.has(`${x+dx}:${r+dr}`)))decor.add(`${x}:${r}`);
}
for(const key of decor){const [x,r]=key.split(':').map(Number),colony=noise(Math.floor(x/2),Math.floor(r/4),5),object=colony<.3?'decor-kelp':colony<.64?'decor-midground-coral':'decor-foreground-coral',direction=['N','E','S','W'][Math.floor(noise(x,r,6)*4)];cells.push({layer:'decor',object,x,y:80-r,direction});}
const map=paintCells({name:'Turquoise passage · Organic 80',columns:7,rows:80,placements:opening},cells,null);
const output=exportMap(map);
const target=new URL('./turquoise-passage-organic-80.json',import.meta.url);
writeFileSync(target,JSON.stringify(output,null,2)+'\n');
const stages=[
 [1,8,'Open launch'],[9,16,'First shelves'],[17,25,'User-authored close turns'],
 [26,34,'Meandering reef throat'],[35,40,'Island fork and recovery'],[41,50,'Offset shelves'],
 [51,68,'Long living cliff'],[69,77,'Final slalom'],[78,80,'Extraction opening'],
].map(([from,to,label])=>{const ps=output.placements.filter(p=>80-p.y>=from&&80-p.y<=to),o=ps.filter(p=>p.layer==='obstacles').length;return {from,to,label,obstacles:o,obstacleDensity:Number((o/((to-from+1)*7)).toFixed(3)),decor:ps.filter(p=>p.layer==='decor').length};});
const evidence=new URL('../../../review/21/organic-80/',import.meta.url);mkdirSync(evidence,{recursive:true});
writeFileSync(new URL('generation.json',evidence),JSON.stringify({source:'design/underwater-map-designer/maps/sources/turquoise-passage-user-reference.json',sourceSha256:createHash('sha256').update(raw).digest('hex'),outputFile:'design/underwater-map-designer/maps/turquoise-passage-organic-80.json',outputSha256:createHash('sha256').update(readFileSync(target)).digest('hex'),outputCounts:{obstacles:output.placements.filter(p=>p.layer==='obstacles').length,decor:output.placements.filter(p=>p.layer==='decor').length},method:'Preserved user rows 1–25; authored organic coast profiles for rows 26–80; deterministic clustered obstacle-attached decor.',preservedOpeningRows:25,grid:output.grid,stages},null,2)+'\n');
console.log(JSON.stringify({file:target.pathname,placements:output.placements.length,stages},null,2));
