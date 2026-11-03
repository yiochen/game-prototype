import {blockTypeByLayer,rowNumber} from './model.js';

function drawBlock(ctx,layer,x,y,cell,paired=false){
 const type=blockTypeByLayer.get(layer);if(!type)return;
 ctx.fillStyle=type.color;
 if(layer==='pickups'){ctx.beginPath();ctx.arc(x+cell/2,y+cell/2,Math.max(4,cell*.28),0,Math.PI*2);ctx.fill();ctx.strokeStyle='#7a5a00';ctx.lineWidth=Math.max(1,cell*.04);ctx.stroke();return;}
 if(layer==='decor'&&paired){
  const inset=Math.max(3,cell*.12),side=Math.max(8,cell*.34);
  ctx.fillRect(x+cell-side-inset,y+inset,side,side);
  ctx.strokeStyle='#163e4b';ctx.lineWidth=Math.max(1,cell*.025);ctx.strokeRect(x+cell-side-inset,y+inset,side,side);
 }else ctx.fillRect(x,y,cell,cell);
}

export function renderMap(canvas,map,view,hover,rect,brush){
 const {width,height,cell,scrollLeft,scrollTop,showObstacles,showDecor,showPickups=true,grid}=view;
 const dpr=Math.min(devicePixelRatio||1,2);if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);}
 const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);ctx.fillStyle='#102f3e';ctx.fillRect(0,0,width,height);
 const origin=mapOrigin(map,width,cell),ox=origin.x-scrollLeft,oy=origin.y-scrollTop;
 const firstX=Math.max(0,Math.floor(-ox/cell)),lastX=Math.min(map.columns,Math.ceil((width-ox)/cell));
 const firstY=Math.max(0,Math.floor(-oy/cell)),lastY=Math.min(map.rows,Math.ceil((height-oy)/cell));
 ctx.fillStyle='#174b5b';ctx.fillRect(ox,oy,map.columns*cell,map.rows*cell);
 const placements=map.placements.filter(p=>p.y>=firstY&&p.y<lastY&&p.x>=firstX&&p.x<lastX&&(p.layer==='obstacles'?showObstacles:p.layer==='pickups'?showPickups:showDecor));
 const obstacles=new Set(placements.filter(p=>p.layer==='obstacles').map(p=>`${p.x}:${p.y}`));
 for(const layer of ['obstacles','decor','pickups'])for(const p of placements)if(p.layer===layer)drawBlock(ctx,layer,ox+p.x*cell,oy+p.y*cell,cell,obstacles.has(`${p.x}:${p.y}`));
 if(grid){ctx.strokeStyle='#bbd7cf45';ctx.lineWidth=1;ctx.beginPath();for(let x=firstX;x<=lastX;x++){ctx.moveTo(Math.round(ox+x*cell)+.5,Math.max(oy,24));ctx.lineTo(Math.round(ox+x*cell)+.5,Math.min(height,oy+map.rows*cell));}for(let y=firstY;y<=lastY;y++){ctx.moveTo(Math.max(ox,28),Math.round(oy+y*cell)+.5);ctx.lineTo(Math.min(width,ox+map.columns*cell),Math.round(oy+y*cell)+.5);}ctx.stroke();}
 if(rect){const x=Math.min(rect.a.x,rect.b.x),y=Math.min(rect.a.y,rect.b.y),w=Math.abs(rect.a.x-rect.b.x)+1,h=Math.abs(rect.a.y-rect.b.y)+1;ctx.fillStyle='#ffe4a62b';ctx.fillRect(ox+x*cell,oy+y*cell,w*cell,h*cell);ctx.strokeStyle='#ffe0a2';ctx.lineWidth=2;ctx.strokeRect(ox+x*cell+1,oy+y*cell+1,w*cell-2,h*cell-2);}
 if(hover&&hover.x>=0&&hover.x<map.columns&&hover.y>=0&&hover.y<map.rows){
  if(brush?.object&&!rect){ctx.globalAlpha=.55;drawBlock(ctx,brush.layer,ox+hover.x*cell,oy+hover.y*cell,cell,obstacles.has(`${hover.x}:${hover.y}`));ctx.globalAlpha=1;}
  ctx.fillStyle=brush?.erase?'#ff7d6b33':'#fff1b913';ctx.fillRect(ox+hover.x*cell,oy+hover.y*cell,cell,cell);ctx.strokeStyle=brush?.erase?'#ffa796':'#ffe1a6';ctx.lineWidth=2;ctx.strokeRect(ox+hover.x*cell+1,oy+hover.y*cell+1,cell-2,cell-2);
 }
 ctx.fillStyle='#102f3ef0';ctx.fillRect(0,0,width,24);ctx.fillRect(0,0,28,height);ctx.font='700 10px Nunito';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#b8d4d6';
 for(let x=firstX;x<lastX;x++)ctx.fillText(String(x+1),ox+(x+.5)*cell,12);
 for(let y=firstY;y<lastY;y++)if(oy+(y+.5)*cell>24)ctx.fillText(String(rowNumber(map,y)),14,oy+(y+.5)*cell);
 return origin;
}
export function mapOrigin(map,width,cell){return {x:Math.max(44,(width-map.columns*cell)/2),y:40};}
