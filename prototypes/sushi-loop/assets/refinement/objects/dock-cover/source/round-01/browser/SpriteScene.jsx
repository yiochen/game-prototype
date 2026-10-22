import React,{useId}from'react';
import {useWorldSpriteRaster}from'../resources/consumer/world-sprite-raster.js';
import {DIRECTIONS,DIRECTION_NAMES,clipFor,spriteFrame,sceneBounds,orderPlacements,placementAtTime,groundRoot,attachmentMarkers,footprintFor,resolveSupportSocket}from'../resources/consumer/sprite-layout.js';
import inputObjects from '../resources/consumer/objects.json';
export const libraryObjects=inputObjects;
export const spriteLibrary={cellSize:128};
export const imageUrl=p=>p?'/'+p:null;
const objectsById=new Map(libraryObjects.map(o=>[o.id,o]));
const primaryClip=o=>o.clips?.find(c=>c.id==='idle')||o.clips?.[0];
const RestaurantBackdrop=()=>null;
export function SpriteScene({ placements, gridSize = [3, 3], seconds = 0, overlays = false, zoom = 1, label, labels = false, floorId, showGrid = true, background = '#eef2ed', animateFloor = false, sceneId, cameraBounds, backdropRenderer = 'uniform35' }) {
  const pattern = useId();
  const cell = spriteLibrary.cellSize || 128;
  const firstObject = libraryObjects.find(object => object.id === placements[0]?.object);
  const underwater = Number(firstObject?.family?.replace('W', '')) >= 11;
  const floor = objectsById.get(floorId || (underwater ? 'floor-underwater' : 'floor-plain')) || (!underwater && objectsById.get('floor-cream'));
  const floorFrame = spriteFrame(floor, floor && primaryClip(floor), 'S', animateFloor ? seconds : 0);
  const floorUrl = imageUrl(floorFrame?.image);
  // A composed world has an authored camera; object studies still include their full capture canvases.
  const supportedPlacements = placements.map(placement => resolveSupportSocket(placement, objectsById));
  const bounds = cameraBounds ? cameraBounds.map(value => value * cell) : sceneBounds(supportedPlacements, libraryObjects, cell, gridSize);
  const timedPlacements = supportedPlacements.map(placement => placementAtTime(placement, seconds, objectsById.get(placement.object)));
  const sprites = orderPlacements(timedPlacements, libraryObjects).map(placement => {
    const object = objectsById.get(placement.object);
    if (!object) return { placement };
    const direction = object.facingPolicy === 'single-player-facing' ? 'S' : placement.direction || 'S';
    const clip = clipFor(object, placement.clip);
    const frame = spriteFrame(object, clip, direction, Math.max(0, seconds + (Number(placement.timeOffset) || 0)));
    const url = imageUrl(frame?.image);
    const [x, y] = groundRoot(placement, object, cell);
    return { placement, object, direction, clip, frame, url, x, y };
  });
  const raster = useWorldSpriteRaster(sprites.filter(sprite => sprite.url).map(({ url, frame, x, y }) => ({
    url, rect: frame.rect, x: x - frame.root[0], y: y - frame.root[1], width: frame.frameSize[0], height: frame.frameSize[1],
  })), bounds);
  return <div className="object-scene-scroll" style={{ background }} tabIndex={0} aria-label={`Pan ${label}`} data-scene-id={sceneId}>
    <svg className="object-tile-scene" style={{ width: `${zoom * 100}%`, background }} viewBox={bounds.join(' ')} role="img" aria-label={label} data-world-raster-ready={raster.ready} data-world-raster-error={raster.error || undefined}>
      <defs><pattern id={pattern} width={cell} height={cell} patternUnits="userSpaceOnUse">{floorUrl && <svg width={cell} height={cell} viewBox={floorFrame.rect.join(' ')} overflow="hidden" preserveAspectRatio="none"><image href={floorUrl} width={floorFrame.atlasSize[0]} height={floorFrame.atlasSize[1]} data-floor-source={floorFrame.image}/></svg>}{showGrid && <path d={`M ${cell} 0 L 0 0 0 ${cell}`} fill="none" stroke="#a8b7b6" strokeWidth="1.5" data-calibration-grid="true"/>}</pattern></defs>
      <rect x="0" y="0" width={gridSize[0] * cell} height={gridSize[1] * cell} fill="#f2f0e6"/>
      <rect x="0" y="0" width={gridSize[0] * cell} height={gridSize[1] * cell} fill={`url(#${pattern})`}/>
      {sceneId === 'restaurant' && <RestaurantBackdrop columns={gridSize[0]} cell={cell} showGrid={showGrid} renderer={backdropRenderer}/>}
      <foreignObject x={raster.plan.x} y={raster.plan.y} width={raster.plan.width / raster.plan.scale} height={raster.plan.height / raster.plan.scale} pointerEvents="none" style={{ visibility: raster.ready ? 'visible' : 'hidden' }} data-world-sprite-raster="true">
        <canvas ref={raster.canvas} style={{ display: 'block', width: '100%', height: '100%' }}/>
      </foreignObject>
      {sprites.map(({ placement, object, direction, clip, frame, url, x, y }, index) => {
        if (!object) return <g key={index}><title>Comparison object {placement.object} is not yet cataloged</title></g>;
        const footprint = footprintFor(object, direction);
        return <g key={placement.id || placement._index} data-placement={placement.id || `${object.id}-${placement._index}`} data-object={object.id} data-direction={direction} data-frame={url ? frame.frame : undefined} data-support-offset={placement.supportSocket ? JSON.stringify(placement.supportOffset) : undefined}>
          <title>{object.name}, {DIRECTION_NAMES[direction]}{url ? `, ${clip.name || clip.id}, frame ${frame.frame + 1} of ${frame.frames}` : ': export pending'}</title>
          {overlays && <rect x={placement.x * cell} y={placement.y * cell} width={footprint[0] * cell} height={footprint[1] * cell} className="object-footprint"/>}
          {url ? <svg x={x - frame.root[0]} y={y - frame.root[1]} width={frame.frameSize[0]} height={frame.frameSize[1]} viewBox={frame.rect.join(' ')} overflow="hidden" preserveAspectRatio="none" data-sprite-source={frame.image} opacity={raster.ready ? 0 : undefined}><image href={url} width={frame.atlasSize[0]} height={frame.atlasSize[1]}/></svg> : <g className="object-export-pending"><rect x={x - cell * .4} y={y - cell * .6} width={cell * .8} height={cell * .8} rx="8"/><text x={x} y={y - cell * .25} textAnchor="middle">Pending</text></g>}
          {overlays && attachmentMarkers(object, clip, direction).map((marker, markerIndex) => <g key={markerIndex} className={`object-attachment is-${marker.kind}`} data-attachment={marker.name}><circle cx={x + marker.position[0]} cy={y + marker.position[1]} r="5"/><text x={x + marker.position[0] + 8} y={y + marker.position[1] - 6}>{marker.name}</text></g>)}
          {overlays && <g className="object-root"><path d={`M ${x - 9} ${y} H ${x + 9} M ${x} ${y - 9} V ${y + 9}`}/><circle cx={x} cy={y} r="3"/></g>}
          {labels && <text className="object-direction-label" x={x} y={cell * gridSize[1] - 12} textAnchor="middle">{DIRECTION_NAMES[direction]}</text>}
        </g>;
      })}
    </svg>
  </div>;
}

