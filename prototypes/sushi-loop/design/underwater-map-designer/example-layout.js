// The designer owns its original example layout independently of game previews.
// Coordinates here retain the original northward route offset used by model.js.
const tile=(object,x,y,direction='S')=>({object,x,y,direction});
const horizontal=(family,x,y,length)=>Array.from({length},(_,i)=>tile(`${family}-${i===0||i===length-1?'end':'middle'}`,x+i,y,i===0?'N':'S'));
export const exampleBarriers=[
 ...horizontal('reef',0,-12,4),
 ...horizontal('wreck',3,-23,4),
 ...Array.from({length:19},(_,i)=>tile(i===18?'rock-wall-corner':i===0?'rock-wall-end':'rock-wall-middle',1,-31-i,i===0?'W':'E')),
 tile('rock-wall-end',0,-49,'N'),
 ...horizontal('rock-shelf',3,-57,4),
 ...horizontal('reef',0,-66,3),
];
