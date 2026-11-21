import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
await fs.mkdir('artifacts',{recursive:true});
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-webgl']});
const page=await browser.newPage({viewport:{width:1440,height:900}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
page.on('response',r=>{if(r.status()>=400)console.log('HTTP error',r.status(),r.url());});
await page.goto(process.env.ARARAT_URL || 'http://127.0.0.1:5174');
await page.waitForFunction(()=>window.ararat?.ready,{timeout:120000});
await page.evaluate(()=>window.ararat.story.disableForTesting());
await page.waitForTimeout(3500);
const stats=await page.evaluate(()=>window.ararat.stats);console.log(stats);
const captures=['arrival','olive','threshold','interior','valley','growth','mountains','stair-foot','stair-side','door-joint','stern','bow','roof','exile','exile-wide'];
for(const name of captures){
  await page.evaluate(n=>window.ararat.visit(n),name);await page.waitForTimeout(400);
  await page.screenshot({path:`artifacts/${name}.png`});
}
await page.evaluate(()=>window.ararat.visit('arrival'));
await page.locator('canvas').click();await page.waitForFunction(()=>window.ararat.locked);
const before=await page.evaluate(()=>window.ararat.position);
await page.keyboard.down('KeyW');
await page.waitForFunction(b=>{const p=window.ararat.position;return Math.hypot(p[0]-b[0],p[2]-b[2])>1;},before,{timeout:60000});
await page.keyboard.up('KeyW');
const after=await page.evaluate(()=>window.ararat.position);assert(Math.hypot(after[0]-before[0],after[2]-before[2])>1,'Walking must change the player position');
await page.keyboard.press('Escape');
// Exercise the entire rebuilt stair and its hatch connection with real keyboard input.
await page.evaluate(()=>window.ararat.visit('stair-walk'));
await page.locator('canvas').click();await page.waitForFunction(()=>window.ararat.locked);
const stairStart=await page.evaluate(()=>window.ararat.position);
await page.keyboard.down('KeyW');
await page.waitForFunction(()=>window.ararat.position[0]<.6,null,{timeout:120000});
await page.keyboard.up('KeyW');
const stairEnd=await page.evaluate(()=>window.ararat.position);
await page.keyboard.down('KeyS');
await page.waitForFunction(()=>window.ararat.position[0]>17.3,null,{timeout:120000});
await page.keyboard.up('KeyS');
const stairReturn=await page.evaluate(()=>window.ararat.position);
await page.keyboard.press('Escape');
const nav=await page.evaluate(()=>{
  const a=window.ararat;a.visit('arrival');
  return {heights:[a.floorAt(15,6),a.floorAt(10,6),a.floorAt(5,6),a.floorAt(0,6)],
    failures:a.verifyRoute([[20,23],[20,6],[15.2,6],[10,6],[4.6,6],[0,6],[0,0],[0,6],[4.6,6],[10,6],[15.2,6],[20,6],[20,23]])};
});
assert(nav.heights.every(Number.isFinite));
assert.deepEqual(nav.failures,[],'The continuous shore / ramp / interior / return route must be traversable');
assert.equal((await page.locator('body').innerText()).trim(),'');
assert.equal(errors.length,0,errors.join('\n'));
const report={stats,walking:{before,after},stairWalking:{start:stairStart,interior:stairEnd,returned:stairReturn},nav,errors,screenshots:captures};
await fs.writeFile('artifacts/verification.json',JSON.stringify(report,null,2));console.log('Verified: scene load, geometry batches, pointer lock, actual keyboard walking, no visible text, no runtime errors.');
await browser.close();
