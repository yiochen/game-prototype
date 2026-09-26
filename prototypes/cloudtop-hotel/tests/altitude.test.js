import test from 'node:test';
import assert from 'node:assert/strict';
import { skyAtHeight, SKY_STAGES } from '../altitude.js';

test('altitude changes continuously through all seven milestones and stays navy beyond 150', () => {
  for (const stage of SKY_STAGES) {
    assert.equal(skyAtHeight(stage.floor).color, stage.color);
    assert.equal(skyAtHeight(stage.floor).stage.name, stage.name);
    if (stage.floor) assert.equal(skyAtHeight(stage.floor - .00001).color, stage.color);
  }
  const lightness = color => color.match(/[\da-f]{2}/g).reduce((sum, channel) => sum + parseInt(channel, 16), 0);
  let last = Infinity;
  for (let floor = 0; floor <= 200; floor += .25) {
    const current = lightness(skyAtHeight(floor).color);
    assert.ok(current <= last); last = current;
  }
  assert.equal(skyAtHeight(10000).color, '#0b1230');
  for (const value of [-20, NaN, Infinity, undefined]) assert.equal(skyAtHeight(value).color, '#398ecb');
});

test('islands recede before starlight and every large cloud is gone by floor 75', () => {
  const ground = skyAtHeight(0), sea = skyAtHeight(25), stars = skyAtHeight(50), summit = skyAtHeight(150);
  assert.equal(ground.islandOpacity, 1); assert.equal(ground.seaOpacity, 0);
  assert.ok(sea.islandOpacity < 1 && sea.islandOpacity > 0);
  assert.ok(sea.islandDrop > 0 && sea.islandScale < 1); assert.equal(sea.seaOpacity, 1);
  assert.equal(stars.islandOpacity, 0);
  assert.ok(stars.cloudDrop > sea.cloudDrop);
  assert.ok(stars.cloudOpacity > 0 && stars.cloudOpacity < sea.cloudOpacity);
  assert.ok(stars.seaOpacity > 0 && stars.seaOpacity < sea.seaOpacity);
  for (const floor of [75, 100, 125, 150, 200]) {
    assert.equal(skyAtHeight(floor).cloudOpacity, 0);
    assert.equal(skyAtHeight(floor).seaOpacity, 0);
  }
  assert.ok(summit.ribbonOpacity > 0); assert.equal(summit.night, 1);
});
