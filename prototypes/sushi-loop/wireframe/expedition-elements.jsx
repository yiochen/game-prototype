import React from 'react';
import { Target, Icon, Money } from './common.jsx';
import './expedition-elements.css';

export const EXPEDITION_COMPONENT_KEYS = [
  'expedition-surroundings', 'expedition-obstacle', 'expedition-pickup',
  'expedition-submarine', 'expedition-creature', 'expedition-hud',
  'expedition-resistance', 'expedition-following-range', 'expedition-attack-warning',
  'expedition-harpoon', 'expedition-resume-countdown', 'expedition-preparation',
  'expedition-catch-reward', 'expedition-route-feature',
];

export function ExpeditionPickup({ className = '', style }) {
  return <span className={`salvage-fragment ${className}`} style={style} role="img" aria-label="Salvage pickup">◇</span>;
}

export function ExpeditionSurroundings({ pickups = true, tunnel = false }) {
  return <><div className="sea-dashes" aria-hidden="true"><i /><i /><i /><i /></div>{!tunnel && <div className="sea-floor" aria-hidden="true"><span>⌁</span><span>♧</span><span>⌁</span><span>♧</span></div>}{pickups && <><ExpeditionPickup className="sf-one" /><ExpeditionPickup className="sf-two" /></>}</>;
}

const obstacleWidths = { small: 18, medium: 32, large: 50 };
const obstacleDepths = { short: 55, medium: 95, long: 140 };
const obstacleForms = { reef: 'reef ridge', boulder: 'rock shelf', wreck: 'wreck section' };
export function ExpeditionObstacle({ kind = 'reef', size = 'large', length = 'long', style = {} }) {
  const width = obstacleWidths[size] || obstacleWidths.large;
  const depth = obstacleDepths[length] || obstacleDepths.long;
  return <div className={`expedition-obstacle obstacle-${kind} obstacle-${size} obstacle-length-${length}`} style={{ width:`${width}%`, height:`${depth}%`, ...style }} role="img" aria-label={`${size[0].toUpperCase()+size.slice(1)} ${obstacleForms[kind] || kind} obstacle`} data-obstacle-size={size} data-obstacle-kind={kind} data-obstacle-length={length} data-obstacle-depth={depth}>
    <svg viewBox="0 0 200 1000" preserveAspectRatio="none" aria-hidden="true">
      {kind === 'reef' ? <><path d="M0 0h176l-14 84 26 95-15 101 20 117-24 82 16 122-25 97 20 98-16 113 11 91H0Z"/><path d="M45 0 29 121 52 249 31 382 53 499 35 651 54 798 37 1000M100 0 117 143 96 286 116 418 95 579 118 739 101 891 115 1000M30 121l86 22M32 382l84 36M35 651l81 88M39 914l72-21" className="obstacle-detail"/></> : kind === 'boulder' ? <><path d="M35 0h116l39 90-14 140 17 126-16 178 16 153-18 168-12 145H29L11 861l17-167-17-141 17-165-15-137 10-143Z"/><path d="M35 0 72 117 45 245 76 391 43 553 77 715 51 862 73 1000M151 0 123 123 151 282 127 437 151 603 122 775 147 1000M72 117l51 6M46 245l105 37M76 391l51 46M43 553l106 50M77 715l45 60M51 862l89 64" className="obstacle-detail"/></> : <><path d="M37 0h126l23 104-6 169 10 153-9 165 5 168-24 241H37L14 759l6-169-9-164 9-153-6-169Z"/><path d="M100 0v1000M34 112h132M31 237h138M33 370h134M31 500h138M34 636h132M35 764h130M43 895h113M52 40v66M148 126v104M53 250v113M150 381v109M54 510v119M145 648v108M58 781v106" className="obstacle-detail"/><path d="m37 552 30-28 20 23 28-22 50 25M31 838l38-27 30 20 36-23 29 23" className="obstacle-detail"/></>}
    </svg>
  </div>;
}

export function ExpeditionTunnelWalls({ wide = false }) {
  return <div className={`expedition-tunnel-walls ${wide ? 'tunnel-walls-wide' : ''}`} role="img" aria-label={wide ? 'Continuous canyon walls around a wider encounter chamber' : 'Continuous underwater canyon walls'}>
    <svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">{wide ? <><path d="M0 0h26l-7 154 17 165-13 183 14 165-17 164 8 169H0Z"/><path d="M1000 0h-26l7 154-17 165 13 183-14 165 17 164-8 169h28Z"/></> : <><path d="M0 0h54l-13 133 23 101-19 114 21 119-24 111 17 133-20 140 14 149H0Z"/><path d="M1000 0h-54l13 133-23 101 19 114-21 119 24 111-17 133 20 140-14 149h53Z"/></>}<path d="M13 0 22 152 11 316 25 482 13 654 22 822 13 1000M987 0 978 152 989 316 975 482 987 654 978 822 987 1000" className="tunnel-wall-detail"/></svg>
  </div>;
}

export function ExpeditionObstacles({ mode = 'travel' }) {
  const chamber = mode === 'encounter';
  return <div className={`expedition-obstacles corridor-${mode}`} data-corridor-mode={mode} role="group" aria-label={chamber ? 'Wide encounter chamber inside the underwater tunnel' : 'Long staggered obstacles around a connected bending underwater passage'}><ExpeditionTunnelWalls wide={chamber}/>{chamber ? <><ExpeditionObstacle kind="reef" size="small" length="long" style={{left:'-14%',top:'-20%'}}/><ExpeditionObstacle kind="wreck" size="small" length="long" style={{right:'-14%',top:'-20%'}}/></> : <><ExpeditionObstacle kind="reef" size="large" length="medium" style={{ left:'0%', top:'-50%' }}/><ExpeditionObstacle kind="wreck" size="medium" length="long" style={{ right:'0%', top:'64%' }}/><ExpeditionObstacle kind="boulder" size="small" length="short" style={{ left:'0%', top:'88%' }}/></>}</div>;
}

export function ExpeditionRouteFeature({ kind = 'current', style = {} }) {
  return <div className={`expedition-route-feature route-${kind}`} style={style} role="img" aria-label={kind === 'current' ? 'Lateral current' : kind === 'boost' ? 'Temporary boost pickup' : 'Optional bonus-passage portal'}>
    <svg viewBox="0 0 100 70" aria-hidden="true">{kind === 'current' ? <><path d="M4 18q20-13 42 0t43 0M4 35q20-13 42 0t43 0M4 52q20-13 42 0t43 0"/><path d="m80 8 12 10-13 8M80 25l12 10-13 8M80 42l12 10-13 8"/></> : kind === 'boost' ? <><circle cx="50" cy="35" r="29"/><path d="M52 12 32 39h15l-1 18 22-28H53Z"/></> : <><ellipse cx="50" cy="35" rx="31" ry="29"/><ellipse cx="50" cy="35" rx="21" ry="21"/><path d="M45 20q21 0 19 18-2 13-15 9-10-3-4-11 3-5 9-2"/><path d="m11 15 7 3M83 54l7 4M82 12l-5 5"/></>}</svg>
  </div>;
}

export function ExpeditionTravelFeatures() {
  return <><ExpeditionRouteFeature kind="portal" style={{ left:'70%', top:'20%' }}/><ExpeditionRouteFeature kind="current" style={{ right:'12%', top:'40%' }}/><ExpeditionRouteFeature kind="boost" style={{ left:'34%', top:'78%' }}/></>;
}

export function ExpeditionHullMeter({ percent = 78, danger = false }) {
  return <div className={`hull-meter ${danger ? 'low-hull' : ''}`} role="meter" aria-label="Hull durability" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}><span>Hull</span><i><b style={{width:`${percent}%`}} /></i></div>;
}

export function ExpeditionHud({ percent = 78, danger = false, salvage = 36 }) {
  return <div className="expedition-hud"><ExpeditionHullMeter percent={percent} danger={danger}/><div className="run-salvage"><Money kind="salvage" amount={salvage}/></div><Target action="navigate" data={{story:'expedition-pause'}} className="icon-control pause-control" title="Pause"><Icon name="pause"/><span className="sr-only">Pause</span></Target></div>;
}

export function ExpeditionResistance({ pursuit = false, percent = pursuit ? 46 : 100, name = 'Eel' }) {
  return <div className="creature-meter" role="meter" aria-label={`${name} resistance`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}><span>{name} · {pursuit ? 'Reeling resistance' : 'Creature resistance'}</span><i><b style={{width:`${percent}%`}}/></i></div>;
}

export function ExpeditionWorldLabel({ label }) { return <div className="expedition-world-label">{label}</div>; }
export function ExpeditionSteeringHint() { return <p className="steering-hint">Drag to steer · illustrated interaction area</p>; }

export function ExpeditionSubmarine({ preparation = false }) {
  return <div className={preparation ? 'prep-sub' : 'expedition-ship'}><Icon name="submarine"/>{preparation ? <span className="battery-ready">Battery full</span> : <span>You</span>}</div>;
}

export function ExpeditionCreature({ state = 'aiming' }) {
  const caught = state === 'caught';
  const hooked = state === 'hooked' || state === 'escaping';
  return <div className={`sea-creature creature-${state} ${state === 'escaping' ? 'escaping' : ''}`} role="img" aria-label={`${state[0].toUpperCase()+state.slice(1)} creature`}><div className="creature-body"><span>•</span><i/></div>{!caught && <small>{hooked ? 'Hooked creature' : 'Shooting window'}</small>}</div>;
}

export function ExpeditionFollowingRange({ danger = false }) {
  return <><div className={`following-strip ${danger ? 'taut' : ''}`}><span>Following range</span></div><div className={`harpoon-cable ${danger ? 'frayed' : ''}`} aria-label={danger ? 'Strained harpoon cable' : 'Attached harpoon cable'} role="img"/></>;
}

export function ExpeditionAttackWarning() {
  return <div className="attack-column" role="img" aria-label="Telegraphed vertical attack warning"><span>Attack warning</span></div>;
}

export function ExpeditionHarpoonProjectile({ style = {} }) {
  return <div className="harpoon-projectile" style={style} role="img" aria-label="Harpoon fired straight ahead"><svg viewBox="0 0 18 64" aria-hidden="true"><path d="M9 61V4M3 13l6-9 6 9M9 22l-5 5"/><path d="M5 39v17M13 47v15" className="projectile-trail"/></svg></div>;
}

export function ExpeditionHarpoonControl({ disabled = false, cooldown = false, firing = false }) {
  return <>{firing && <ExpeditionHarpoonProjectile/>}<Target action="navigate" data={{story:'expedition-pursuit'}} className={`harpoon-control ${cooldown ? 'harpoon-cooling' : ''}`} disabled={disabled || cooldown} title={cooldown ? 'Harpoon cooling down' : 'Harpoon'}><span className="harpoon-control-icon"><Icon name="harpoon"/>{cooldown && <svg className="harpoon-cooldown-ring" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="19"/><circle className="harpoon-cooldown-progress" cx="22" cy="22" r="19"/></svg>}</span><strong>Harpoon</strong></Target></>;
}

export function ExpeditionResumeCountdown({ number = 3 }) {
  return <div className="resume-countdown" role="status"><strong>{number}</strong><span>Returning to ship...</span></div>;
}

export function ExpeditionPreparationAirlock() {
  return <Target action="navigate" data={{story:'restaurant-live'}} className="prep-airlock"><span className="airlock"><Icon name="arrow-left"/><b>Sushi Bar</b><small>Return before departure</small></span></Target>;
}

export function ExpeditionStartControl() {
  return <div className="start-action"><Target action="navigate" data={{story:'expedition-travel'}} className="primary-action" title="Start"><Icon name="play"/><strong>Start</strong></Target><p>Begin a new expedition</p></div>;
}

export function ExpeditionPreparation() {
  return <><h2 className="underwater-title">Ready to depart</h2><ExpeditionPreparationAirlock/><ExpeditionSubmarine preparation/><ExpeditionStartControl/></>;
}

export function ExpeditionCatchReward({ repeat = false }) {
  return <div className="catch-focus"><span className="catch-rings" aria-hidden="true"/><ExpeditionCreature state="caught"/><h2>Catch secured</h2><p>{repeat ? 'A familiar creature' : 'First discovery'}</p>{repeat && <span className="repeat-reward"><Money kind="salvage" amount={18}/><small>Repeat-catch bonus</small></span>}</div>;
}

function Example({ label, children, className = '' }) {
  return <section className="component-example expedition-component-example"><h3>{label}</h3><div className={`expedition-element-demo ocean-scene ${className}`}>{children}</div></section>;
}

export function ExpeditionElementExamples({ component, state = {} }) {
  switch (component) {
    case 'expedition-surroundings': return <><Example label="Continuous canyon walls and water depth"><ExpeditionTunnelWalls/><ExpeditionSurroundings pickups={false} tunnel/><ExpeditionWorldLabel label="Travelling"/><ExpeditionSteeringHint/></Example><Example label="Wider creature encounter chamber"><ExpeditionTunnelWalls wide/><ExpeditionSurroundings pickups={false} tunnel/></Example></>;
    case 'expedition-obstacle': return <>{['reef','boulder','wreck'].flatMap(kind=>['small','medium','large'].map((size,index)=>{const length=['short','medium','long'][index];return <Example key={`${kind}-${size}`} label={`${obstacleForms[kind]} · ${obstacleWidths[size]}% wide · ${obstacleDepths[length]}% deep`} className="obstacle-element-demo"><ExpeditionObstacle kind={kind} size={size} length={length} style={{left:`${(100-obstacleWidths[size])/2}%`,top:length==='long' ? '-20%' : length==='medium' ? '3%' : '22%'}}/></Example>;}))}<Example label="Connected tunnel passage · free lateral steering" className="obstacle-corridor-demo corridor-travel"><ExpeditionSurroundings tunnel/><ExpeditionObstacles/><ExpeditionSubmarine/><ExpeditionTravelFeatures/></Example></>;
    case 'expedition-pickup': return <Example label="Salvage pickup" className="pickup-element-demo"><ExpeditionPickup style={{left:'48%',top:'40%'}}/></Example>;
    case 'expedition-submarine': return <><Example label="Travelling submarine"><ExpeditionSubmarine/></Example><Example label="Ready before departure"><ExpeditionSubmarine preparation/></Example></>;
    case 'expedition-creature': return <>{['aiming','hooked','escaping','caught'].map(mode=><Example key={mode} label={`${mode[0].toUpperCase()+mode.slice(1)} creature`} className="creature-element-demo"><ExpeditionCreature state={mode}/></Example>)}</>;
    case 'expedition-hud': return <><Example label="Hull, run salvage and Pause" className="hud-element-demo"><ExpeditionHud/></Example><Example label="Low hull stays local to its meter" className="hud-element-demo"><ExpeditionHud danger percent={22}/></Example></>;
    case 'expedition-resistance': return <><Example label="Aiming · full resistance" className="resistance-element-demo"><ExpeditionResistance/></Example><Example label="Following · remaining resistance" className="resistance-element-demo"><ExpeditionResistance pursuit/></Example></>;
    case 'expedition-following-range': return <><Example label="Following strip and attached cable"><ExpeditionFollowingRange/><ExpeditionCreature state="hooked"/><ExpeditionSubmarine/></Example><Example label="Out of range · strained cable"><ExpeditionFollowingRange danger/><ExpeditionCreature state="escaping"/><ExpeditionSubmarine/></Example></>;
    case 'expedition-attack-warning': return <Example label="Attack lane leaves room inside following range"><ExpeditionFollowingRange/><ExpeditionAttackWarning/><ExpeditionCreature state="hooked"/><ExpeditionSubmarine/></Example>;
    case 'expedition-harpoon': return <><Example label="Ready · fresh press fires" className="harpoon-element-demo"><ExpeditionHarpoonControl/></Example><Example label="Cooling down · circular fill" className="harpoon-element-demo"><ExpeditionHarpoonControl cooldown/></Example><Example label="Projectile · straight toward screen top" className="harpoon-element-demo"><ExpeditionHarpoonControl firing/></Example></>;
    case 'expedition-resume-countdown': return <Example label="Saved expedition resumes after countdown"><ExpeditionSubmarine/><ExpeditionResumeCountdown/></Example>;
    case 'expedition-preparation': return <Example label="Ready ship, Sushi Bar airlock and Start" className="preparation-element-demo"><ExpeditionSurroundings/><ExpeditionPreparation/></Example>;
    case 'expedition-catch-reward': return <><Example label="First discovery" className="catch-element-demo"><ExpeditionCatchReward/></Example><Example label="Repeat catch · extra salvage" className="catch-element-demo"><ExpeditionCatchReward repeat/></Example></>;
    case 'expedition-route-feature': return <>{['current','boost','portal'].map(kind=><Example key={kind} label={kind === 'current' ? 'Lateral current' : kind === 'boost' ? 'Temporary travel boost' : 'Optional safe bonus passage'} className="route-element-demo"><ExpeditionRouteFeature kind={kind} style={{left:'30%',top:'35%'}}/></Example>)}</>;
    default: return null;
  }
}
