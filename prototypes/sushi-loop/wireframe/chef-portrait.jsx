import React from 'react';
import lena from '../assets/ui/chef-portraits/v1/lena-front.png';
import omar from '../assets/ui/chef-portraits/v1/omar-front.png';
import ama from '../assets/ui/chef-portraits/v1/ama-front.png';
import mateo from '../assets/ui/chef-portraits/v1/mateo-front.png';
import noor from '../assets/ui/chef-portraits/v1/noor-front.png';
import dalia from '../assets/ui/chef-portraits/v1/dalia-front.png';
import ellis from '../assets/ui/chef-portraits/v1/ellis-front.png';
import rowan from '../assets/ui/chef-portraits/v1/rowan-front.png';
import './chef-portrait.css';

export const chefPortraits = [
  {id:'lena',name:'Lena Brooks',src:lena},{id:'omar',name:'Omar Haddad',src:omar},
  {id:'ama',name:'Ama Mensah',src:ama},{id:'mateo',name:'Mateo Rivera',src:mateo},
  {id:'noor',name:'Noor Haddad',src:noor},{id:'dalia',name:'Dalia Farouk',src:dalia},
  {id:'ellis',name:'Ellis Morgan',src:ellis},{id:'rowan',name:'Rowan McLeod',src:rowan},
];
export const chefPortraitFor = value => chefPortraits.find(p=>p.id===value || p.name===value);
export function ChefPortrait({chefId,name,bust=false,className='',...rest}) {
  const chef=chefPortraitFor(chefId || name);
  if(!chef)return null;
  return <span {...rest} className={`chef-portrait ${bust?'chef-portrait--bust':''} ${className}`} role="img" aria-label={`${chef.name}, front view${bust?', chest up':''}`}><img src={chef.src} alt="" draggable="false"/></span>;
}
export function ChefPortraitGallery() {
  return <div className="chef-portrait-gallery"><header><h2>Chef front views</h2><p>Existing Blender models · eye-level orthographic camera · shared fixed scale</p><p>Full front view for inventory and applications; the same render clipped to the chest for recipe headers.</p></header><div className="chef-portrait-cards">{chefPortraits.map(chef=><section key={chef.id}><h3>{chef.name}</h3><div className="chef-portrait-pair"><figure><ChefPortrait chefId={chef.id}/><figcaption>Full front</figcaption></figure><figure><ChefPortrait chefId={chef.id} bust/><figcaption>Chest up</figcaption></figure></div></section>)}</div></div>;
}
