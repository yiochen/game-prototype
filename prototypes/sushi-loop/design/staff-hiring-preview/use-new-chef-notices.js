import {useEffect} from 'react';
export const NEW_CHEF_SEEN_MS=1400;

export function useNewChefNotices({staff,strip,enabled,onSeen}){
 const unread=staff.filter(chef=>chef.isNew).map(chef=>chef.id).join('|');
 useEffect(()=>{
  const root=strip.current;if(!enabled||!root||!unread)return;
  const timers=new Map(),visible=new Set(),ids=new Set(unread.split('|'));
  const stop=id=>{clearTimeout(timers.get(id));timers.delete(id);};
  const start=id=>{
   if(timers.has(id)||document.visibilityState!=='visible')return;
   timers.set(id,setTimeout(()=>{timers.delete(id);if(visible.has(id)&&document.visibilityState==='visible')onSeen([id]);},NEW_CHEF_SEEN_MS));
  };
  const observer=new IntersectionObserver(entries=>{for(const entry of entries){const id=entry.target.dataset.chef;if(entry.isIntersecting&&entry.intersectionRatio>=.85){visible.add(id);start(id);}else{visible.delete(id);stop(id);}}},{root,threshold:[0,.85,1]});
  for(const card of root.querySelectorAll('[data-chef]'))if(ids.has(card.dataset.chef))observer.observe(card);
  const suspend=()=>{for(const id of timers.keys())stop(id);};
  const resume=()=>{if(document.visibilityState==='visible')for(const id of visible)start(id);};
  const visibility=()=>document.visibilityState==='visible'?resume():suspend();
  document.addEventListener('visibilitychange',visibility);window.addEventListener('blur',suspend);window.addEventListener('focus',resume);
  return()=>{observer.disconnect();suspend();document.removeEventListener('visibilitychange',visibility);window.removeEventListener('blur',suspend);window.removeEventListener('focus',resume);};
 },[unread,enabled,strip,onSeen]);
}
