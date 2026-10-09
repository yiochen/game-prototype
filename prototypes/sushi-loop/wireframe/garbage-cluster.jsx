import React from 'react';
import { Target, Money } from './common.jsx';
import './garbage-cluster.css';

function footprint(id, name, mask, cost) {
  const cells = mask.flatMap((row, y) => [...row].flatMap((occupied, x) => occupied === '1' ? [{x, y}] : []));
  return {id, name, cost, columns:Math.max(...mask.map(row => row.length)), rows:mask.length, cells};
}

// Authored review fixtures; costs do not calculate or simulate the game's economy.
export const garbageClusterFixtures = [
  footprint('small', 'Small garbage cluster', ['11','11'], 80),
  footprint('broad', 'Wide garbage cluster', ['1111','1111'], 160),
  footprint('large', 'Irregular garbage cluster', ['011','111','111','110'], 240),
];

export function garbageClusterFor(id) {
  return garbageClusterFixtures.find(cluster => cluster.id === id) || garbageClusterFixtures[2];
}

function DebrisCell({ index }) {
  const turn = [-7,5,-3,8][index % 4];
  return <g className="debris-cell" transform={`rotate(${turn} 22 22)`}>
    <path className="debris-paper" d="m3 6 16-3 5 5-2 16-17 3-3-10z"/><path d="m5 10 12-2M7 14l10-2M8 18l9-2M18 3v6l6-1"/>
    {index % 3 === 0 ? <><path className="debris-bag" d="m29 12 2-3 6 1-1 5q9 8 6 20-8 7-18 0-2-11 5-23z"/><path d="m29 15 7 1M28 21l-2 10M36 20l2 10"/></> : index % 3 === 1 ? <><path className="debris-box" d="m20 12 13-3 9 7-1 18-16 6-9-9z"/><path d="m20 12 6 9 16-5M26 21l-1 19M32 10l-3 9M31 23l7-2v7l-7 2z"/></> : <><path className="debris-bucket" d="m23 15 16 1-1 21-14 1z"/><ellipse cx="31" cy="16" rx="8" ry="3"/><path d="M27 23v9M34 23v9M25 15q5-16 12 1"/></>}
    <path className="debris-plank" d="m1 29 32-7 2 5-32 8z"/><path d="m5 31 22-5M8 31l-1 2M28 25l-1 2"/>
    <path className="debris-can" d="m9 30 5-1 3 9-5 2z"/><path d="m10 32 5-1M12 36l4-1"/>
    <path className="debris-fragment" d="m3 39 4-3 3 5-4 1zM35 5l5-2 2 5-5 2zM20 36l2 4-4 2-2-3z"/>
  </g>;
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
    {cluster.cells.map(({x,y}, index) => <g key={`${x},${y}`} transform={`translate(${x*44} ${y*44})`}><rect className="garbage-cell-ground" width="44" height="44"/><DebrisCell index={index + cluster.id.length}/></g>)}
    <path className="garbage-footprint-outline" d={outsideEdges(cluster)}/>
  </svg>;
  const classes = `garbage-cluster ${interactive ? 'clearance-target' : 'garbage-cluster-preview'} ${selected ? 'garbage-cluster-selected' : ''} ${className}`;
  return interactive ? <Target action="navigate" data={{story:'expansion',value:cluster.id,garbageClusterId:cluster.id,...(panel === undefined ? {} : {garbagePanel:panel})}} className={classes} title={`Inspect ${cluster.name.toLowerCase()}`} style={dimensions}>{art}</Target> : <div className={classes} role="img" aria-label={`${cluster.name}${selected ? ' selected for clearing' : ''}`} style={dimensions}>{art}</div>;
}

export function GarbageClusterExamples({ state = {} }) {
  return <><section className="component-example garbage-cluster-balance"><h3>Restaurant coins</h3><Money amount={state.coinBalance ?? 1240}/></section>{garbageClusterFixtures.filter(cluster => !state.clearedGarbageClusterIds?.includes(cluster.id)).map(cluster => <section key={cluster.id} className="component-example garbage-cluster-example"><h3>{cluster.name}</h3><GarbageCluster cluster={cluster}/></section>)}</>;
}
