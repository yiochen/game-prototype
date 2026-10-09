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

export function ExpeditionSurroundings({ pickups = true }) {
  return <><div className="sea-dashes" aria-hidden="true"><i /><i /><i /><i /></div><div className="sea-floor" aria-hidden="true"><span>⌁</span><span>♧</span><span>⌁</span><span>♧</span></div>{pickups && <><ExpeditionPickup className="sf-one" /><ExpeditionPickup className="sf-two" /></>}</>;
}

const obstacleWidths = { small: 18, medium: 32, large: 50 };
export function ExpeditionObstacle({ kind = 'reef', size = 'large', style = {} }) {
  const width = obstacleWidths[size] || obstacleWidths.large;
  return <div className={`expedition-obstacle obstacle-${kind} obstacle-${size}`} style={{ width:`${width}%`, ...style }} role="img" aria-label={`${size[0].toUpperCase()+size.slice(1)} ${kind} obstacle`} data-obstacle-size={size} data-obstacle-kind={kind}>
    <svg viewBox="0 0 200 100" aria-hidden="true">
      {kind === 'reef' ? <><path d="M2 97V72l17-8 6-26 24 5 12-27 26 7 13 19 25-5 19 13 28-7 26 25v29Z"/><path d="m22 79 21-14 25 9 19-17 22 22 31-18 26 13M60 25l9 18M104 91l4-12M147 57l6 11" className="obstacle-detail"/></> : kind === 'boulder' ? <><path d="m16 85-9-37 23-28 32-14 67 5 46 20 18 41-34 23H61Z"/><path d="m30 22 29 26-15 37M59 48l52-15 41 35M129 12l-18 21 3 55M152 68l32 2" className="obstacle-detail"/></> : <><path d="m3 75 34 20h125l35-23-27-22H25Z"/><path d="M57 51V29h75v22M82 28V8h12v20M109 50V36h13v14M47 61l13 14M82 62l8 14M127 60l8 17M165 62l-8 13" className="obstacle-detail"/><path d="m42 94 13-14 20 13 16-15 18 15" className="obstacle-detail"/></>}
    </svg>
  </div>;
}

export function ExpeditionObstacles() {
  return <div className="expedition-obstacles" aria-label="Route obstacles with a clear right-side passage"><ExpeditionObstacle kind="reef" size="large" style={{ left:'0%', top:'67%' }}/><ExpeditionObstacle kind="wreck" size="medium" style={{ left:'3%', top:'34%' }}/><ExpeditionObstacle kind="boulder" size="small" style={{ right:'7%', top:'20%' }}/></div>;
}

export function ExpeditionRouteFeature({ kind = 'current', style = {} }) {
  return <div className={`expedition-route-feature route-${kind}`} style={style} role="img" aria-label={kind === 'current' ? 'Lateral current' : kind === 'boost' ? 'Temporary boost pickup' : 'Optional bonus-passage portal'}>
    <svg viewBox="0 0 100 70" aria-hidden="true">{kind === 'current' ? <><path d="M4 18q20-13 42 0t43 0M4 35q20-13 42 0t43 0M4 52q20-13 42 0t43 0"/><path d="m80 8 12 10-13 8M80 25l12 10-13 8M80 42l12 10-13 8"/></> : kind === 'boost' ? <><circle cx="50" cy="35" r="29"/><path d="M52 12 32 39h15l-1 18 22-28H53Z"/></> : <><ellipse cx="50" cy="35" rx="31" ry="29"/><ellipse cx="50" cy="35" rx="21" ry="21"/><path d="M45 20q21 0 19 18-2 13-15 9-10-3-4-11 3-5 9-2"/><path d="m11 15 7 3M83 54l7 4M82 12l-5 5"/></>}</svg>
  </div>;
}

export function ExpeditionTravelFeatures() {
  return <><ExpeditionRouteFeature kind="portal" style={{ left:'13%', top:'23%' }}/><ExpeditionRouteFeature kind="current" style={{ right:'8%', top:'36%' }}/><ExpeditionRouteFeature kind="boost" style={{ right:'14%', top:'52%' }}/></>;
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
    case 'expedition-surroundings': return <Example label="Ocean, depth dashes and sea floor"><ExpeditionSurroundings pickups={false}/><ExpeditionWorldLabel label="Travelling"/><ExpeditionSteeringHint/></Example>;
    case 'expedition-obstacle': return <>{['reef','boulder','wreck'].flatMap(kind=>['small','medium','large'].map(size=><Example key={`${kind}-${size}`} label={`${kind[0].toUpperCase()+kind.slice(1)} · ${size} · ${obstacleWidths[size]}% width`} className="obstacle-element-demo"><ExpeditionObstacle kind={kind} size={size} style={{left:`${(100-obstacleWidths[size])/2}%`,top:'30%'}}/></Example>))}</>;
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
