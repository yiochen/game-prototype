import React from 'react';
import { Target, Icon, Money } from './common.jsx';
import './expedition-elements.css';

export const EXPEDITION_COMPONENT_KEYS = [
  'expedition-surroundings', 'expedition-tile', 'expedition-obstacle', 'expedition-pickup',
  'expedition-submarine', 'expedition-creature', 'expedition-hud',
  'expedition-resistance', 'expedition-following-range', 'expedition-attack-warning',
  'expedition-harpoon', 'expedition-resume-countdown', 'expedition-preparation',
  'expedition-catch-reward', 'expedition-route-feature',
];

export const EXPEDITION_GRID_COLUMNS = 10;

export function ExpeditionTileGrid({ children, className = '' }) {
  return <div className={`expedition-tile-grid ${className}`} data-grid-columns={EXPEDITION_GRID_COLUMNS}><div className="expedition-water-grid" aria-hidden="true"/>{children}</div>;
}

export function ExpeditionTile({ kind = 'reef', segment = 'middle', edge = 'inside', collidable = true, anchor = 'floor', layer = 'midground', column = 0, row = 0 }) {
  const decoration = !collidable;
  return <span className={`expedition-tile tile-${kind} tile-${segment} tile-edge-${edge} ${decoration ? `tile-decoration decor-${layer}` : 'tile-collider'}`} data-tile-kind={kind} data-tile-role={segment} data-grid-column={column} data-grid-row={row} data-collidable={String(collidable)} data-anchor={anchor} data-decor-layer={decoration ? layer : undefined} aria-hidden="true"><svg viewBox="0 0 100 100" aria-hidden="true">
    {kind === 'kelp' ? <><path d="M46 98q-23-20-11-40T29 15M51 99q21-28 6-49T63 4M47 91q-3-27 16-38T76 19" className="tile-kelp"/></> : kind === 'coral' ? <><path d="M52 94V36M52 64 28 47V24M52 77 77 56V34M52 44 38 29V12M77 56l12-15M28 47 15 34" className="tile-coral"/><circle cx="38" cy="12" r="5"/><circle cx="77" cy="33" r="5"/></> : kind === 'column' ? <><path d="M23 0h54v100H23Z"/><path d="M35 0v100M65 0v100" className="tile-detail"/>{segment === 'start' && <path d="m23 12 15-8 12 12L64 6l13 8" className="tile-detail"/>}{segment === 'end' && <path d="M18 86h64v14H18Z"/>}</> : kind === 'wreck' ? <><rect x="0" y="0" width="100" height="100"/><path d="M0 26h100M0 74h100M50 0v100M18 0v24M82 27v46M18 75v25" className="tile-detail"/>{segment !== 'middle' && <path d={segment === 'start' ? 'M0 6h100M6 6v20M94 6v20' : 'M0 94h100M6 74v20M94 74v20'} className="tile-run-cap"/>}</> : <><rect x="0" y="0" width="100" height="100"/><path d={kind === 'boulder' ? 'M17 0 34 22 18 52 39 79 28 100M72 0 57 27 80 50 61 79 74 100M18 52l39-25M39 79l41-29' : 'M31 0 21 26 39 52 24 81 33 100M75 0 60 28 77 58 59 86 69 100M21 26l39 2M39 52l38 6M24 81l35 5'} className="tile-detail"/>{kind === 'reef' && <><circle cx="12" cy="67" r="8"/><circle cx="90" cy="36" r="7"/></>}{segment !== 'middle' && <path d={segment === 'start' ? 'M0 6h100' : 'M0 94h100'} className="tile-run-cap"/>}</>}
  </svg></span>;
}

export function ExpeditionTileBlock({ kind = 'reef', column = 0, row = 0, columns = 1, rows = 1, anchor = 'floor', collidable = true, layer = 'midground', label, className = '', ...data }) {
  const cells = Array.from({length:rows}, (_, y) => Array.from({length:columns}, (_, x) => <ExpeditionTile key={`${x}-${y}`} kind={kind} segment={y === 0 ? 'start' : y === rows-1 ? 'end' : 'middle'} edge={x === 0 ? 'left' : x === columns-1 ? 'right' : 'inside'} column={column+x} row={row+y} anchor={anchor} collidable={collidable} layer={layer}/>));
  return <div className={`expedition-tile-block ${className}`} style={{'--grid-column':column,'--grid-row':row,'--grid-columns':columns,'--grid-rows':rows}} role="img" aria-label={label || `${columns} by ${rows} ${kind} ${collidable ? 'collider' : 'decoration'}`} data-grid-column={column} data-grid-row={row} data-grid-columns={columns} data-grid-rows={rows} data-collidable={String(collidable)} data-anchor={anchor} data-decor-layer={collidable ? undefined : layer} {...data}>{cells}</div>;
}

export function ExpeditionPickup({ className = '', style }) {
  return <span className={`salvage-fragment ${className}`} style={style} role="img" aria-label="Salvage pickup">◇</span>;
}

export function ExpeditionSurroundings({ pickups = true, tunnel = false }) {
  return <><div className="sea-dashes" aria-hidden="true"><i /><i /><i /><i /></div><ExpeditionTileBlock kind="kelp" column={0} row={5} collidable={false} anchor="wall" layer="background" label="Background kelp decoration"/><ExpeditionTileBlock kind="coral" column={9} row={9} collidable={false} anchor="wall" layer="midground" label="Midground coral decoration"/>{!tunnel && <ExpeditionTileBlock kind="kelp" column={0} row={15} columns={1} rows={2} collidable={false} layer="foreground" label="Foreground kelp decoration"/>}{pickups && <><ExpeditionPickup className="sf-one" /><ExpeditionPickup className="sf-two" /></>}</>;
}

const obstacleColumns = { small: 2, medium: 3, large: 5 };
const obstacleRows = { short: 12, medium: 20, long: 28 };
const obstacleForms = { reef: 'reef ridge', boulder: 'rock shelf', wreck: 'wreck section' };
export function ExpeditionObstacle({ kind = 'reef', size = 'large', length = 'long', column = 0, row = 0 }) {
  const columns = obstacleColumns[size] || obstacleColumns.large;
  const rows = obstacleRows[length] || obstacleRows.long;
  return <ExpeditionTileBlock kind={kind} column={column} row={row} columns={columns} rows={rows} anchor={kind === 'reef' ? 'wall' : 'floor'} className={`expedition-obstacle obstacle-${kind} obstacle-${size} obstacle-length-${length}`} label={`${size[0].toUpperCase()+size.slice(1)} ${obstacleForms[kind] || kind} obstacle`} data-obstacle-size={size} data-obstacle-kind={kind} data-obstacle-length={length}/>;
}

export function ExpeditionTunnelWalls({ wide = false }) {
  return <div className={`expedition-tunnel-walls ${wide ? 'tunnel-walls-wide' : ''}`} role="group" aria-label={wide ? 'Continuous tile walls around a wider encounter chamber' : 'Continuous underwater tile canyon walls'}><ExpeditionTileBlock kind="boulder" column={0} row={-4} columns={1} rows={40} anchor="wall" label="Left connected tile wall"/><ExpeditionTileBlock kind="boulder" column={9} row={-4} columns={1} rows={40} anchor="wall" label="Right connected tile wall"/></div>;
}

export function ExpeditionObstacles({ mode = 'travel' }) {
  const chamber = mode === 'encounter';
  return <div className={`expedition-obstacles corridor-${mode}`} data-corridor-mode={mode} role="group" aria-label={chamber ? 'Wide encounter chamber inside the underwater tile tunnel' : 'Connected tile obstacles around a bending underwater passage'}><ExpeditionTunnelWalls wide={chamber}/>{chamber ? <><ExpeditionObstacle kind="reef" size="small" length="long" column={-1} row={-4}/><ExpeditionObstacle kind="wreck" size="small" length="long" column={9} row={-4}/></> : <><ExpeditionObstacle kind="reef" size="large" length="medium" column={0} row={-10}/><ExpeditionObstacle kind="wreck" size="medium" length="long" column={7} row={15}/><ExpeditionObstacle kind="boulder" size="small" length="short" column={0} row={21}/></>}</div>;
}

export function ExpeditionRouteFeature({ kind = 'current', style = {} }) {
  return <div className={`expedition-route-feature route-${kind}`} style={style} role="img" aria-label={kind === 'current' ? 'Lateral current' : kind === 'boost' ? 'Temporary boost pickup' : 'Optional bonus-passage portal'}>
    <svg viewBox="0 0 100 70" aria-hidden="true">{kind === 'current' ? <><path d="M4 18q20-13 42 0t43 0M4 35q20-13 42 0t43 0M4 52q20-13 42 0t43 0"/><path d="m80 8 12 10-13 8M80 25l12 10-13 8M80 42l12 10-13 8"/></> : kind === 'boost' ? <><circle cx="50" cy="35" r="29"/><path d="M52 12 32 39h15l-1 18 22-28H53Z"/></> : <><ellipse cx="50" cy="35" rx="31" ry="29"/><ellipse cx="50" cy="35" rx="21" ry="21"/><path d="M45 20q21 0 19 18-2 13-15 9-10-3-4-11 3-5 9-2"/><path d="m11 15 7 3M83 54l7 4M82 12l-5 5"/></>}</svg>
  </div>;
}

export function ExpeditionTravelFeatures() {
  return <><ExpeditionRouteFeature kind="portal" style={{ left:'70cqw', top:'50cqw' }}/><ExpeditionRouteFeature kind="current" style={{ left:'60cqw', top:'105cqw' }}/><ExpeditionRouteFeature kind="boost" style={{ left:'40cqw', top:'170cqw' }}/></>;
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
  return <section className="component-example expedition-component-example"><h3>{label}</h3><ExpeditionTileGrid className={`expedition-element-demo ocean-scene ${className}`}>{children}</ExpeditionTileGrid></section>;
}

export function ExpeditionElementExamples({ component, state = {} }) {
  switch (component) {
    case 'expedition-surroundings': return <><Example label="Continuous canyon walls and water depth"><ExpeditionTunnelWalls/><ExpeditionSurroundings pickups={false} tunnel/><ExpeditionWorldLabel label="Travelling"/><ExpeditionSteeringHint/></Example><Example label="Wider creature encounter chamber"><ExpeditionTunnelWalls wide/><ExpeditionSurroundings pickups={false} tunnel/></Example></>;
    case 'expedition-tile': return <><Example label="1×1 rock · floor anchor" className="tile-footprint-demo"><ExpeditionTileBlock kind="boulder" column={4} row={2} columns={1} rows={1}/></Example><Example label="1×2 column · two connected square cells" className="tile-footprint-demo"><ExpeditionTileBlock kind="column" column={4} row={1} columns={1} rows={2}/></Example><Example label="2×2 rock cluster · floor anchor" className="tile-footprint-demo"><ExpeditionTileBlock kind="boulder" column={4} row={1} columns={2} rows={2}/></Example><Example label="Connected runs · start, middle and end tiles" className="tile-run-demo"><ExpeditionTileBlock kind="reef" column={2} row={1} columns={2} rows={6} anchor="wall"/><ExpeditionTileBlock kind="wreck" column={6} row={1} columns={2} rows={6}/></Example><Example label="Wall anchors · connected edge tiles" className="tile-run-demo"><ExpeditionTunnelWalls/><ExpeditionTileBlock kind="reef" column={1} row={2} columns={1} rows={3} anchor="wall"/></Example><Example label="Visual decor · background, midground, foreground" className="tile-run-demo"><ExpeditionTileBlock kind="kelp" column={1} row={1} collidable={false} layer="background"/><ExpeditionTileBlock kind="coral" column={4} row={3} collidable={false} layer="midground"/><ExpeditionTileBlock kind="kelp" column={7} row={5} collidable={false} layer="foreground"/></Example></>;
    case 'expedition-obstacle': return <>{['reef','boulder','wreck'].flatMap(kind=>['small','medium','large'].map((size,index)=>{const length=['short','medium','long'][index];return <Example key={`${kind}-${size}`} label={`${obstacleForms[kind]} · ${obstacleColumns[size]}×${obstacleRows[length]} connected tiles`} className="obstacle-element-demo"><ExpeditionObstacle kind={kind} size={size} length={length} column={Math.floor((EXPEDITION_GRID_COLUMNS-obstacleColumns[size])/2)} row={1}/></Example>;}))}<Example label="Connected tile tunnel · free lateral steering" className="obstacle-corridor-demo corridor-travel"><ExpeditionSurroundings tunnel/><ExpeditionObstacles/><ExpeditionSubmarine/><ExpeditionTravelFeatures/></Example></>;
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
