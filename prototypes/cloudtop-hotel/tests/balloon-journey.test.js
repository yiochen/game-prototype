import test from 'node:test';
import assert from 'node:assert/strict';
import { balloonJourneys, balloonPose, BALLOON_DURATION } from '../balloon-journey.js';

const state = suits => ({ links: suits.map((suit,id)=>({suit,id})), nextLinkId:suits.length });
test('balloons belong to new neighborhoods, including repeated types, never extensions',()=>{
  const before=state(['bunny','frog']);
  assert.deepEqual(balloonJourneys(before,state(['bunny','frog','frog']),500),[]);
  const journeys=balloonJourneys(before,state(['bunny','frog','frog','cat','bunny','cat']),500);
  assert.deepEqual(journeys.map(j=>[j.id,j.suit,j.end-1]),[[3,'cat',3],[4,'bunny',4],[5,'cat',5]]);
  assert.ok(journeys.every((j,i)=>j.startAt>500 && (!i || j.startAt>journeys[i-1].startAt)));
});
test('a balloon emerges at its floor and joins the live dock after a readable flight',()=>{
  const journey=balloonJourneys(state([]),state(['frog']),500)[0];
  const source={x:230,y:620}, dock={x:160,y:40,width:35,height:51};
  const at=age=>balloonPose(journey,journey.startAt+age,source,dock,72,390);
  assert.equal(at(-1),null);
  assert.equal(at(0).x,source.x);
  assert.equal(at(0).stage,'emerging');
  assert.ok(BALLOON_DURATION>=2200);
  const stages=new Set(); let previousY=Infinity;
  for(let age=800;age<=BALLOON_DURATION;age+=20) {
    const p=at(age); stages.add(p.stage);
    assert.ok(p.y<=previousY+.01); previousY=p.y;
    assert.ok(p.x-p.width/2>=0 && p.x+p.width/2<=390);
  }
  assert.ok(stages.has('rising') && stages.has('docking'));
  const arrival=at(BALLOON_DURATION);
  assert.equal(arrival.stage,'arrived'); assert.equal(arrival.alpha,0);
  assert.equal(arrival.x,dock.x); assert.equal(arrival.y,dock.y);
  assert.equal(arrival.width,dock.width); assert.equal(arrival.height,dock.height);
});
