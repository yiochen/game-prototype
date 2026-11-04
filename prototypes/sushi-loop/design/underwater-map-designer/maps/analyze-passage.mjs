// Independent footprint check in progress coordinates: row 1 is the map bottom.
// This checks geometric clearance and a lateral-change bound, not native gameplay.
export function findPassage(map,{fromRow=1,toRow=map.rows,width=.64,length=.88,maxLateralPerRow=10}={}){
 const obstacles=map.placements.filter(p=>p.layer==='obstacles').map(p=>({x:p.x,z:map.rows-p.y-1}));
 const hw=width/2,hh=length/2,scale=20,first=Math.ceil(hw*scale),last=Math.floor((map.columns-hw)*scale),start=fromRow-.5,end=toRow-.5,frames=Math.round((end-start)*10),reach=Math.floor(maxLateralPerRow*scale/10+1e-8);
 let previous=new Uint8Array(last+1),count=0;
 for(let frame=0;frame<=frames;frame++){
  const z=start+frame/10,near=obstacles.filter(o=>Math.abs(z-o.z-.5)<.5+hh-1e-8),next=new Uint8Array(last+1),prefix=new Uint16Array(last+2);
  for(let i=0;i<=last;i++)prefix[i+1]=prefix[i]+previous[i];
  count=0;
  for(let i=first;i<=last;i++){
   const x=i/scale,free=!near.some(o=>Math.abs(x-o.x-.5)<.5+hw-1e-8);
   const canReach=frame===0?(fromRow===1?Math.abs(x-map.columns/2)<.001:true):(prefix[Math.min(last,i+reach)+1]-prefix[Math.max(0,i-reach)]>0);
   if(free&&canReach){next[i]=1;count++;}
  }
  if(!count)return {passable:false,failedAtProgressRow:Number((z+.5).toFixed(2)),width,length,maxLateralPerRow};
  previous=next;
 }
 return {passable:true,fromRow,toRow,width,length,maxLateralPerRow,finishPositions:count};
}
