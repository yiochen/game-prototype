import React,{useLayoutEffect,useRef} from 'react';
import rubberStamp from './assets/hiring-stamp.png';
import inkFrame from './assets/assigned-stamp.png';

// Transaction state commits before this presentation. Cancelling a visual never
// reverses payment/recruitment or marks an obscured inventory photo as seen.
export function ApplicationCardSurface({entry,onExit,children}){
 const surface=useRef(null),prop=useRef(null),imprint=useRef(null);
 useLayoutEffect(()=>{
  const element=surface.current,reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hire=entry.phase==='hire',exit=entry.phase==='exit',enter=entry.phase==='enter';
  const x=entry.fromX||0,y=entry.fromY||0,opacity=entry.fromOpacity??1;
  if(hire){
   element.dataset.presence='hiring';
   const duration=reduced?650:1280;
   const paperFrames=reduced?[{opacity},{opacity:1,offset:.85},{opacity:0}]:[
    {opacity,transform:`translate(${x}px,${y}px) rotate(0deg) scale(1)`,offset:0,easing:'cubic-bezier(.16,1,.3,1)'},
    {opacity:1,transform:'translate(0,0) rotate(0deg) scale(1.045)',offset:.15},
    {opacity:1,transform:'translate(0,0) rotate(0deg) scale(1.045)',offset:.3,easing:'ease-out'},
    {opacity:1,transform:'translate(0,2px) rotate(0deg) scale(1.025)',offset:.33,easing:'ease-out'},
    {opacity:1,transform:'translate(0,0) rotate(0deg) scale(1.045)',offset:.4},
    {opacity:1,transform:'translate(0,0) rotate(0deg) scale(1.045)',offset:.76,easing:'cubic-bezier(.4,0,1,1)'},
    {opacity:0,transform:'translate(-90px,-145px) rotate(-16deg) scale(.92)',offset:1}
   ];
   const inkFrames=reduced?[{opacity:0},{opacity:.94,offset:.16},{opacity:.94}]:[
    {opacity:0,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.18)',offset:0},
    {opacity:0,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.18)',offset:.31},
    {opacity:1,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.08)',offset:.33,easing:'ease-out'},
    {opacity:.94,transform:'translate(-50%,-50%) rotate(-12deg) scale(1)',offset:.4},
    {opacity:.94,transform:'translate(-50%,-50%) rotate(-12deg) scale(1)',offset:1}
   ];
   const paper=element.animate(paperFrames,{duration,fill:'both'});
   const ink=imprint.current.animate(inkFrames,{duration,fill:'both'});
   const tool=reduced?null:prop.current.animate([
    {opacity:0,transform:'translateY(-170px) rotate(-5deg) scale(1.1)',offset:0},
    {opacity:0,transform:'translateY(-170px) rotate(-5deg) scale(1.1)',offset:.15},
    {opacity:1,transform:'translateY(-150px) rotate(-5deg) scale(1.1)',offset:.17,easing:'cubic-bezier(.45,0,.9,.55)'},
    {opacity:1,transform:'translateY(0) rotate(0deg) scale(1)',offset:.32,easing:'ease-out'},
    {opacity:1,transform:'translateY(-11px) rotate(-2deg) scale(1)',offset:.37,easing:'ease-in-out'},
    {opacity:1,transform:'translateY(-4px) rotate(-1deg) scale(1)',offset:.42,easing:'ease-in'},
    {opacity:0,transform:'translateY(-175px) rotate(-9deg) scale(1.06)',offset:.58},
    {opacity:0,transform:'translateY(-175px) rotate(-9deg) scale(1.06)',offset:1}
   ],{duration,fill:'both'});
   paper.finished.then(()=>onExit(entry.candidate.id,entry.serial)).catch(()=>{});
   return()=>{paper.cancel();ink.cancel();tool?.cancel();};
  }
  const frames=reduced
   ?[{opacity:enter?0:opacity},{opacity:exit?0:1}]
   :exit
    ?[{opacity,transform:`translate(${x}px,${y}px) rotate(0deg) scale(1)`},{opacity:0,transform:`translate(${x-18}px,${y+52}px) rotate(-7deg) scale(.94)`}]
    :[{opacity:enter?0:opacity,transform:`translate(${enter?24:x}px,${enter?24:y}px) rotate(${enter?4:0}deg) scale(${enter?.97:1})`},{opacity:1,transform:'translate(0,0) rotate(0deg) scale(1)'}];
  element.dataset.presence=exit?'exiting':enter?'entering':'moving';
  const animation=element.animate(frames,{duration:reduced?80:exit?210:280,delay:!reduced?entry.delay||0:0,easing:exit?'cubic-bezier(.4,0,1,1)':'cubic-bezier(.16,1,.3,1)',fill:'both'});
  animation.finished.then(()=>{if(exit)onExit(entry.candidate.id,entry.serial);else element.dataset.presence='settled';}).catch(()=>{});
  return()=>animation.cancel();
 },[entry.serial]);
 return <div className="application-card-visual" ref={surface}>{children}{entry.phase==='hire'&&<div className="hire-confirmation" aria-hidden="true"><div className="hired-imprint" ref={imprint}><img src={inkFrame} alt=""/><span>Hired</span></div><img className="hire-rubber-stamp" ref={prop} src={rubberStamp} alt=""/></div>}</div>;
}
