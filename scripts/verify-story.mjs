import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-webgl']});
const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];
page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
await page.goto(process.env.ARARAT_URL||'http://127.0.0.1:5174');
await page.waitForFunction(()=>window.ararat?.ready&&window.ararat.story?.snapshot.reading,null,{timeout:120000});
async function visiblePassage(){await page.waitForFunction(()=>!window.ararat.story.snapshot.reading||window.ararat.story.snapshot.textState==='visible',null,{timeout:15000});}
async function intermediateFade(){
  const handle=await page.waitForFunction(()=>{
    const el=document.querySelector('#manuscript'),style=getComputedStyle(el),opacity=Number(style.opacity);
    if(opacity>.02&&opacity<.98)return {opacity,verticalTranslation:new DOMMatrixReadOnly(style.transform).m42,top:el.getBoundingClientRect().top};
    return false;
  },null,{timeout:10000});
  const sample=await handle.jsonValue();await handle.dispose();return sample;
}
const initialFade=await intermediateFade();assert.equal(initialFade.verticalTranslation,0);
await visiblePassage();await page.waitForTimeout(1400);
const font=await page.locator('.memory-ink').evaluate(el=>({family:getComputedStyle(el).fontFamily,size:getComputedStyle(el).fontSize,loaded:document.fonts.check('36px "Caveat Brush"')}));
assert(font.family.includes('Caveat Brush')&&font.loaded);assert(parseFloat(font.size)>=28);
await page.screenshot({path:'artifacts/story-prologue.png'});
// A page must fade away completely before its words are replaced. Extra input is ignored.
const first=await page.evaluate(()=>({snapshot:window.ararat.story.snapshot,top:document.querySelector('#manuscript').getBoundingClientRect().top}));
await page.locator('.story-passage').click();
const outgoingFade=await intermediateFade();assert.equal(outgoingFade.verticalTranslation,0);assert(Math.abs(outgoingFade.top-first.top)<.1);
await page.keyboard.press('KeyE');
assert.equal(await page.evaluate(()=>window.ararat.story.snapshot.pageIndex),first.snapshot.pageIndex,'Rapid input must not skip a fading passage');
assert.equal(await page.evaluate(()=>window.ararat.story.snapshot.text),first.snapshot.text,'Words stay in place during fade-out');
await page.waitForFunction(()=>window.ararat.story.snapshot.pageIndex===1&&window.ararat.story.snapshot.textState==='visible',null,{timeout:15000});
async function readPages(){
  for(let i=0;i<12;i++){
    await visiblePassage();const before=await page.evaluate(()=>window.ararat.story.snapshot);if(!before.reading)return;
    await page.locator('.story-passage').click();
    await page.waitForFunction(p=>{const s=window.ararat.story.snapshot;return !s.reading||(s.textState==='visible'&&(s.pageIndex!==p.pageIndex||s.text!==p.text));},before,{timeout:15000});
  }
  throw new Error('Narrative did not release the passage');
}
await readPages();
await page.evaluate(()=>window.ararat.visit('exile'));await page.keyboard.press('KeyE');
await page.waitForFunction(()=>window.ararat.story.snapshot.reading);
await visiblePassage();
assert.match(await page.locator('.memory-ink').innerText(),/could not leave/);
await readPages();assert.equal(await page.evaluate(()=>window.ararat.story.snapshot.phase),'explore','Departure must be gated before exploration');
for(const [view,id] of [['olive','olive'],['linen-memory','linen'],['rope-memory','rope']]){
  await page.evaluate(n=>window.ararat.visit(n),view);await page.keyboard.press('KeyE');
  await page.waitForFunction(()=>window.ararat.story.snapshot.reading);await visiblePassage();
  await page.screenshot({path:`artifacts/story-${id}.png`});await readPages();
  assert((await page.evaluate(()=>window.ararat.story.snapshot.memories)).includes(id));
}
await page.evaluate(()=>window.ararat.visit('exile'));await page.keyboard.press('KeyE');
await page.waitForFunction(()=>window.ararat.story.snapshot.reading);await visiblePassage();
await page.screenshot({path:'artifacts/story-departure.png'});await readPages();
await page.waitForFunction(()=>window.ararat.story.snapshot.phase==='voyage');
const start=await page.evaluate(()=>window.ararat.story.snapshot.boatPosition);
await page.waitForFunction(p=>{const q=window.ararat.story.snapshot.boatPosition;return Math.hypot(q[0]-p[0],q[2]-p[2])>1;},start,{timeout:60000});
await page.evaluate(()=>window.ararat.story.setVoyageTimeForTesting(27));await page.waitForTimeout(1600);
await page.screenshot({path:'artifacts/story-sunset.png'});
await page.evaluate(()=>window.ararat.story.setVoyageTimeForTesting(36));
await page.waitForFunction(()=>window.ararat.story.snapshot.reading);
await visiblePassage();
assert.match(await page.locator('.memory-ink').innerText(),/never arrived/);
await page.screenshot({path:'artifacts/story-ending.png'});await readPages();
assert.equal(await page.evaluate(()=>window.ararat.story.snapshot.phase),'afloat');
await page.waitForTimeout(700);await page.screenshot({path:'artifacts/story-afterglow.png'});
const final=await page.evaluate(()=>window.ararat.story.snapshot);assert.equal(errors.length,0,errors.join('\n'));
await page.waitForFunction(()=>window.ararat.story.snapshot.phase==='returning'&&window.ararat.story.snapshot.blackOpacity>.15&&window.ararat.story.snapshot.blackOpacity<.9,null,{timeout:30000});
await page.screenshot({path:'artifacts/story-fade-to-black.png'});
await page.waitForFunction(()=>{const s=window.ararat.story.snapshot;return s.phase==='returning'&&s.homeReset&&s.blackOpacity>.999;},null,{timeout:30000});
const underBlack=await page.evaluate(()=>({story:window.ararat.story.snapshot,camera:window.ararat.position}));
assert.deepEqual(underBlack.story.memories,[]);assert(Math.hypot(...underBlack.camera.map((v,i)=>v-underBlack.story.homePosition[i]))<.001,'Camera resets only under full black');
await page.screenshot({path:'artifacts/story-black.png'});
await page.waitForFunction(()=>{const s=window.ararat.story.snapshot;return s.phase==='prologue'&&s.reading&&s.loopCount===1;},null,{timeout:30000});
const restartedFade=await intermediateFade();assert.equal(restartedFade.verticalTranslation,0);await visiblePassage();
const restarted=await page.evaluate(()=>window.ararat.story.snapshot);
assert.match(restarted.text,/The water withdrew/);assert.equal(restarted.blackOpacity,0);assert.deepEqual(restarted.memories,[]);assert.deepEqual(restarted.boatPosition,first.snapshot.boatPosition);
await page.screenshot({path:'artifacts/story-restart.png'});
assert.equal(errors.length,0,errors.join('\n'));
await fs.writeFile('artifacts/story-verification.json',JSON.stringify({font,proseFades:{initialFade,outgoingFade,restartedFade,noVerticalSlide:true,rapidInputGuarded:true},departureGated:true,memories:final.memories,boatActuallyMoved:true,endingReached:true,final,returnLoop:{underBlack,restarted},returnedToOpening:true,errors},null,2));
console.log('Story verified: slow opacity-only passages, guarded page changes, all memories, sunset ending, full black and a clean return to the opening.');await browser.close();
