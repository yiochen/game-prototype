import React from 'react';
import lena from '../assets/ui/chef-headshots/v1/raw/lena.png';
import omar from '../assets/ui/chef-headshots/v1/raw/omar.png';
import ama from '../assets/ui/chef-headshots/v1/raw/ama.png';
import mateo from '../assets/ui/chef-headshots/v1/raw/mateo.png';
import noor from '../assets/ui/chef-headshots/v1/raw/noor.png';
import dalia from '../assets/ui/chef-headshots/v1/raw/dalia.png';
import ellis from '../assets/ui/chef-headshots/v1/raw/ellis.png';
import rowan from '../assets/ui/chef-headshots/v1/raw/rowan.png';
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
  return <span {...rest} className={`chef-portrait ${bust?'chef-portrait--bust':''} ${className}`} role="img" aria-label={`${chef.name}, illustrated headshot${bust?', dialog crop':''}`}><img src={chef.src} alt="" draggable="false"/></span>;
}
export function ChefPortraitGallery() {
  return <div className="chef-portrait-gallery"><header><h2>Chef headshots</h2><p>ImageGen concept-art family · transparent illustrated profiles</p><p>Shared across inventory, applications and profiles. The recipe header anchors its headshot to the separator and lets it extend above the popup.</p></header><div className="chef-portrait-cards">{chefPortraits.map(chef=><section key={chef.id}><h3>{chef.name}</h3><div className="chef-portrait-pair"><figure><ChefPortrait chefId={chef.id}/><figcaption>Headshot</figcaption></figure><figure><ChefPortrait chefId={chef.id} bust/><figcaption>Dialog crop</figcaption></figure></div></section>)}</div></div>;
}
