import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createNavigation} from '../src/navigation.js';
const data=JSON.parse(fs.readFileSync('public/assets/navigation.json','utf8'));
const ground=(x,z)=>{const y=-z;return .14*Math.sin(x*.23)*Math.cos(y*.15)+.09*Math.cos(y*.4)+.005*(y+15)-Math.max(0,-y-26)*.07-Math.max(0,-x-22)*.045;};
const nav=createNavigation(data,ground),s=data.stairs;
for(let i=0;i<s.count;i++){
  const x=s.xBottom-(i+.5)*(s.xBottom-s.xTop)/s.count;
  assert.equal(nav.surfaceAt(x,6).kind,'stair');
  assert(Math.abs(nav.heightAt(x,6)-(s.zBottom+(i+1)*(s.zTop-s.zBottom)/s.count))<1e-9);
  assert.equal(nav.surfaceAt(x,7.1).kind,'ground','No invisible walking surface outside the guard line');
}
assert.equal(nav.heightAt(s.xTop,6),data.deck.z);
assert.equal(nav.heightAt(4,6),data.deck.z,'A real platform must overlap the hull deck');
for(const y of [-20,-19,-15,0,15,19,20]){
  const width=nav.deckWidth(y);
  assert.equal(nav.surfaceAt(width-.05,-y).kind,'deck');
  assert.equal(nav.surfaceAt(width+.05,-y).kind,'ground','The narrow ends must not retain the previous rectangular ghost deck');
}
assert.equal(nav.surfaceAt(5,15).kind,'ground');
console.log('Navigation verified: all 28 tread heights, both platform joins, stair guard limits and tapered deck boundaries.');
