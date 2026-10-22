import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';
import{spriteFrame,clipFor,groundRoot,footprintFor,orderPlacements,sceneBounds}from'../round-02/resources/consumer/sprite-layout.js';
export const H=path.dirname(fileURLToPath(import.meta.url)),O=path.resolve(H,'../..');
export const objects=JSON.parse(fs.readFileSync(path.join(H,'../round-02/resources/consumer/objects.json')));
Object.assign(objects.find(o=>o.id==='dock-cover'),{renderPass:'overhead',height:2.2});
export const casePlan=JSON.parse(fs.readFileSync(path.join(O,'inputs/shared-world-pose-v1/plan.json')));
export const humanSupports=Object.freeze({'approach':null,'first-tread':'dock-entry','second-tread':'dock-entry','terminal-tread':'dock-deck','transfer':'dock-deck','front-deck':'dock-deck','front-right-branch':'dock-deck','right-apron':'dock-deck','exterior-stop':'dock-deck'});
export function orderedSprites(placements,d,clip,index,human){
 const order=orderPlacements(placements,objects),sprites=order.map(p=>{const o=objects.find(o=>o.id===p.object),cl=clipFor(o,p.clip),seconds=p.object==='customer-rosa'?human.publishedClipIndex/12:index/12,f=spriteFrame(o,cl,d,seconds),[x,y]=groundRoot(p,o,128);return{id:p.object,key:`${p.object}/${cl.id}/${d}`,rect:f.rect,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1],actualFrameIndex:f.frame,sourceProjection:p.object==='submarine-yellow'?65:p.object==='customer-rosa'?35:55.00797980144134};});
 return{order:order.map(p=>p.object),sprites};
}
export function setup(d,clip,index,mode,phase=0,pan=0,human=casePlan.cases.find(c=>c.id==='exterior-stop')){
 if(!Object.hasOwn(humanSupports,human.id))throw Error('Unsupported human fixture');
 const a={N:Math.PI,E:Math.PI/2,S:0,W:-Math.PI/2}[d],roots={'dock-floor':[0,0,0],'dock-entry':[0,-1.5,0],'submarine-yellow':[-.7,-.42,.23],'workshop-hut':[.78,.35,.23],'dock-cover':[0,0,.23],'customer-rosa':[...human.sourceFacingXY,human.solvedRootZ]};
 const placements=Object.entries(roots).map(([id,[x,y,z]])=>{const o=objects.find(o=>o.id===id),rc=o.directionRootCells?.[d]||o.rootCell||footprintFor(o,d).map(n=>n/2),wx=Math.cos(a)*x-Math.sin(a)*y,wy=Math.sin(a)*x+Math.cos(a)*y,support=id==='customer-rosa'?humanSupports[human.id]:['submarine-yellow','workshop-hut','dock-cover'].includes(id)?'dock-deck':null;return{object:id,direction:d,x:1.5+wx-rc[0],y:1.5-wy-rc[1],offset:[phase,-z*89.6+phase],clip:id==='dock-cover'?clip:id==='submarine-yellow'?mode:id==='customer-rosa'?human.actorClip:'static',...(id==='dock-floor'?{id:'dock-deck'}:{}),...(support?{supportedBy:support}:{})};});
 // Frozen layout accepts an object id only when its placement is unique.
 if(placements.filter(p=>p.object==='dock-entry').length!==1)throw Error('Entry support must identify one placement');
 const baseline=placements.map(p=>({...p,offset:[p.offset[0]-phase,p.offset[1]-phase]})),bounds=sceneBounds(baseline,objects,128,[3,3]);bounds[0]+=pan;bounds[1]+=pan;
 return{placements,bounds,...orderedSprites(placements,d,clip,index,human)};
}
