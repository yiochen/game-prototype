// Review fixtures only. Native gameplay/content integration follows UI approval.
export const floor = {columns:21,rows:13,starterColumns:7,backdropRows:3};
export const patches = [
 {id:'sofa-west',name:'Broken sofa',art:'garbage-sofa',x:7,y:3,w:3,h:3,price:240},
 {id:'dock-access',name:'Wrecked car',art:'garbage-car',x:7,y:6,w:3,h:3,price:180,access:true},
 {id:'shelves-west',name:'Collapsed shelving',art:'garbage-shelving',x:7,y:9,w:3,h:4,price:300},
 {id:'shelves-middle',name:'Collapsed shelving',art:'garbage-shelving',x:10,y:3,w:4,h:3,price:360},
 {id:'sofa-middle',name:'Broken sofa',art:'garbage-sofa',x:10,y:6,w:4,h:3,price:280},
 {id:'car-middle',name:'Wrecked car',art:'garbage-car',x:10,y:9,w:4,h:4,price:420},
 {id:'car-east',name:'Wrecked car',art:'garbage-car',x:14,y:3,w:4,h:3,price:480},
 {id:'shelves-east',name:'Collapsed shelving',art:'garbage-shelving',x:14,y:6,w:4,h:3,price:400},
 {id:'sofa-east',name:'Broken sofa',art:'garbage-sofa',x:14,y:9,w:4,h:4,price:340},
 {id:'sofa-edge',name:'Broken sofa',art:'garbage-sofa',x:18,y:3,w:3,h:3,price:380},
 {id:'car-edge',name:'Wrecked car',art:'garbage-car',x:18,y:6,w:3,h:3,price:520},
 {id:'shelves-edge',name:'Collapsed shelving',art:'garbage-shelving',x:18,y:9,w:3,h:4,price:440},
];
export const economy={startingCoins:120,reviewCoins:640,saleCoins:14,saleSeconds:8};
export const dockCells=Array.from({length:9},(_,i)=>[7+i%3,6+Math.floor(i/3)]);
// Decoration roots are outside the actual room, never on panel/viewport divisions.
export const decorations=[
 ...Array.from({length:10},(_,i)=>({id:`left-${i}`,art:['plant-angular','crate-wood','barrel-wood','lantern-gold','slate-rock'][i%5],x:-.8,y:3.5+i})),
 ...Array.from({length:10},(_,i)=>({id:`right-${i}`,art:['slate-rock','plant-angular','sign-blank','barrel-wood','lantern-gold'][i%5],x:21.7,y:3.5+i})),
 ...[0,2,5,8,11,14,17,20].map((x,i)=>({id:`bottom-${i}`,art:['plant-angular','barrel-wood','crate-wood','lantern-gold','sign-blank'][i%5],x:x+.5,y:13.9})),
];
