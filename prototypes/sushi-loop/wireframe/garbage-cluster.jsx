import React from 'react';
import { Target, Money } from './common.jsx';
import './garbage-cluster.css';

function footprint(id, name, mask, cost) {
  const cells = mask.flatMap((row, y) => [...row].flatMap((occupied, x) => occupied === '1' ? [{x, y}] : []));
  return {id, name, cost, columns:Math.max(...mask.map(row => row.length)), rows:mask.length, cells};
}

// Authored review fixtures; costs do not calculate or simulate the game's economy.
export const garbageClusterFixtures = [
  footprint('small', 'Broken sofa garbage cluster', ['11','11'], 80),
  footprint('broad', 'Wrecked car garbage cluster', ['1111','1111'], 160),
  footprint('large', 'Collapsed shelving garbage cluster', ['011','111','111','110'], 240),
];

export function garbageClusterFor(id) {
  return garbageClusterFixtures.find(cluster => cluster.id === id) || garbageClusterFixtures[2];
}

function BrokenSofa() {
  return <g className="garbage-object-art" data-garbage-object="sofa">
    <ellipse className="junk-shadow" cx="44" cy="68" rx="35" ry="8"/>
    <path className="junk-wood" d="m20 60 7 1-1 13-6-1zM62 60l7 2-3 8-5-1z"/>
    <path className="junk-fabric" d="M15 39 14 22q0-11 12-10l33 3q15 0 14 13l-4 16Z"/>
    <path d="m23 16 2 19M42 17l-1 18M63 19l-2 17M16 29l8-3"/>
    <path className="junk-soft" d="m47 20 4 3 4-1-2 5 3 4-6-1-4 3 1-6-3-3z"/>
    <path className="junk-fabric-dark" d="m14 39 50-2 10 14-7 15-48-4-8-11z"/>
    <path className="junk-fabric" d="m19 38 22 2-2 18-21-3-3-8zM43 40l21-2 6 10-6 13-22-3z"/>
    <path d="m22 44 12 2M45 49l5-2 4 4 5-2M41 40l-2 18"/>
    <path className="junk-soft" d="m51 47 3 1 3-3 2 4 4 1-4 3-1 4-4-3-3 1 1-4z"/>
    <path className="junk-fabric" d="M68 37q3-8 10-4l4 9-1 20-9 4-5-15Z"/>
    <path d="m74 39 3 12-1 9"/>
    <path className="junk-fabric-dark" d="M5 43q-1-11 7-12l7 3 2 13-7 11-9-4Z"/>
    <path d="m10 36 4 9-3 8M19 37l4-1 3 3"/>
    <path className="junk-wood" d="m6 73 26 5-1 5-25-5z"/><path d="m11 77 14 3"/>
    <path className="junk-metal" d="m73 71 7-1 3 10-8 3z"/><path d="m74 73 6-1M76 78l5-1"/>
    <path className="junk-soft" d="m45 71 4-3 3 3 4-1 1 4-4 3-2-2-4 1z"/>
  </g>;
}

function WreckedCar() {
  return <g className="garbage-object-art" data-garbage-object="car">
    <ellipse className="junk-shadow" cx="90" cy="73" rx="77" ry="7"/>
    <path className="junk-metal" d="m12 35 29-4 16-16 32-1 22 16 26 2 22-7 9 17-8 20-26 3-20-1-61 5-27-2-13-10Z"/>
    <path className="junk-glass" d="m47 31 13-12 15 1-1 12zM80 20l8-1 16 13-24 1z"/>
    <path d="m89 22-5 7 7-2 4 5M61 20l4 11M43 35l9 23M79 35l-1 22M83 40l12-1"/>
    <path className="junk-metal-light" d="m125 31 12-18 25 4-12 17-12 4Z"/>
    <path d="m136 16 22 4M134 23l18 4"/>
    <path className="junk-dark" d="m129 36 24-3 8 10-9 6-23-5Z"/>
    <path d="m137 37 5 8M149 36l-3 8M129 48l14 3M157 46l7 2"/>
    <path className="junk-metal-light" d="m111 34 13 3-4 5 6 6-9 4-10-3 3-7z"/>
    <path d="m14 43 15 1M15 49l8 1M30 35l-5 6 4 9-5 8M88 51l8-5 6 6"/>
    <path className="junk-dark" d="m11 52 14 1 4 10-14-3zM152 52l15-3-2 8-15 4"/>
    <circle className="junk-tire" cx="46" cy="63" r="14"/><circle className="junk-metal-light" cx="46" cy="63" r="7"/><path d="m42 61 7 4M48 59l-3 8"/>
    <ellipse className="junk-tire" cx="133" cy="64" rx="15" ry="12" transform="rotate(-9 133 64)"/><ellipse className="junk-metal-light" cx="133" cy="64" rx="8" ry="5" transform="rotate(-9 133 64)"/><path d="m128 65 10-2"/>
    <path className="junk-metal" d="m2 70 21-2 3 5-22 3z"/><path d="m6 71 12-1"/>
    <path className="junk-glass" d="m76 73 5-3 2 7zM87 78l5-6 3 7zM106 75l4-5 3 4z"/>
    <path className="junk-paper" d="m154 73 13-3 5 7-12 7-6-3z"/><path d="m159 74 6 4M158 79l3-1"/>
  </g>;
}

function CollapsedShelving() {
  return <g className="garbage-object-art" data-garbage-object="shelving">
    <path className="junk-shadow" d="m20 134 43-111 62 13-39 125-40 5-25-16Z"/>
    <path className="junk-wood-dark" d="m58 8 63 15-45 135-65-26Z"/>
    <path className="junk-wood" d="m58 8 7 2-47 124-7-2zM115 22l6 1-15 45-5 3-2 15 3-2-12 34-7 3-13 35 6 2 9-26 8-2 10-36 6-6 2-20z"/>
    <path className="junk-paper" d="m64 19 12 3-6 20-13-2z"/><path d="m63 23 9 3M61 29l8 2M60 35l7 2"/>
    <path className="junk-metal" d="m87 29 9-1 8 17-11 6-7-13z"/><path d="m89 31 7-1M94 40l6-2"/>
    <path className="junk-wood" d="m45 42 64 16-3 9-64-16z"/><path d="m50 48 47 12"/>
    <path className="junk-fabric" d="m52 60 18 4 6 12-5 9-26-5-3-10z"/><path d="m50 67 17 4M51 75l7-4 7 7"/>
    <path className="junk-metal-light" d="m85 69 10 4-7 16-9-4z"/><path d="m86 74 6 3"/>
    <path className="junk-wood" d="m31 78 65 17-4 9-65-17z"/><path d="m36 84 45 12"/>
    <path className="junk-paper" d="m40 95 22 5-8 21-22-5z"/><path d="m39 102 15 4M37 108l11 3M36 113l7 2"/>
    <path className="junk-metal" d="m70 105 11 1-3 18-11-3z"/><ellipse cx="75" cy="107" rx="5" ry="2"/>
    <path className="junk-wood" d="m18 114 45 12-2 9-46-12zM73 130l11 3-4 9-10-4 1-4z"/><path d="m23 120 29 8M64 133l6-3"/>
    <path className="junk-wood" d="m11 132 17 6-3 10-9-5-3 1-5-5zM36 142l40 16-4 9-41-15z"/><path d="m41 149 25 10"/>
    <path className="junk-dark" d="m108 103 3-5 7 3-1 6q11 9 9 18-6 8-19 3-10-5-4-18Z"/><path d="m108 107 8 2M108 114l-2 8M118 113l3 9"/>
    <path className="junk-metal-light" d="m17 66 6-3 6 13-8 3z"/><path d="m21 69 5 7"/>
    <path className="junk-paper" d="m3 103 15-3 6 8-6 7-13-4z"/><path d="m7 105 9 3M8 109l5 1"/>
    <path className="junk-wood" d="m6 163 45 5-1 6-44-5z"/><path d="m14 167 25 3"/>
  </g>;
}

function ClusterObject({ id }) {
  if (id === 'small') return <BrokenSofa/>;
  if (id === 'broad') return <WreckedCar/>;
  return <CollapsedShelving/>;
}

function outsideEdges(cluster) {
  const occupied = new Set(cluster.cells.map(({x,y}) => `${x},${y}`));
  return cluster.cells.flatMap(({x,y}) => {
    const left=x*44, top=y*44, right=left+44, bottom=top+44;
    return [
      !occupied.has(`${x},${y-1}`) && `M${left} ${top}H${right}`,
      !occupied.has(`${x+1},${y}`) && `M${right} ${top}V${bottom}`,
      !occupied.has(`${x},${y+1}`) && `M${right} ${bottom}H${left}`,
      !occupied.has(`${x-1},${y}`) && `M${left} ${bottom}V${top}`,
    ].filter(Boolean);
  }).join(' ');
}

export function GarbageCluster({ cluster = garbageClusterFor('large'), interactive = true, selected = false, panel, className = '', style }) {
  const dimensions = {width:`${cluster.columns*44}px`, height:`${cluster.rows*44}px`, ...style};
  const art = <svg className="garbage-cluster-art" viewBox={`-3 -3 ${cluster.columns*44+6} ${cluster.rows*44+6}`} preserveAspectRatio="none" aria-hidden="true">
    <g className="garbage-occupancy-grid">{cluster.cells.map(({x,y}) => <rect key={`${x},${y}`} className="garbage-cell-ground" x={x*44} y={y*44} width="44" height="44"/>)}</g>
    <ClusterObject id={cluster.id}/>
    <path className="garbage-footprint-outline" d={outsideEdges(cluster)}/>
  </svg>;
  const classes = `garbage-cluster ${interactive ? 'clearance-target' : 'garbage-cluster-preview'} ${selected ? 'garbage-cluster-selected' : ''} ${className}`;
  return interactive ? <Target action="navigate" data={{story:'expansion',value:cluster.id,garbageClusterId:cluster.id,...(panel === undefined ? {} : {garbagePanel:panel})}} className={classes} title={`Inspect ${cluster.name.toLowerCase()}`} style={dimensions}>{art}</Target> : <div className={classes} role="img" aria-label={`${cluster.name}${selected ? ' selected for clearing' : ''}`} style={dimensions}>{art}</div>;
}

export function GarbageClusterExamples({ state = {} }) {
  return <><section className="component-example garbage-cluster-balance"><h3>Restaurant coins</h3><Money amount={state.coinBalance ?? 1240}/></section>{garbageClusterFixtures.filter(cluster => !state.clearedGarbageClusterIds?.includes(cluster.id)).map(cluster => <section key={cluster.id} className="component-example garbage-cluster-example"><h3>{cluster.name}</h3><GarbageCluster cluster={cluster}/></section>)}</>;
}
