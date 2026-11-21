import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const url=process.env.ARARAT_URL||'https://noahisarider.github.io/ararat/';
const chrome='C:/Program Files/Google/Chrome/Application/chrome.exe';
const hasChrome=await fs.access(chrome).then(()=>true,()=>false);
const browser=await chromium.launch({...(hasChrome?{executablePath:chrome}:{}),headless:true,args:['--enable-webgl']});
try{
  const page=await browser.newPage({viewport:{width:1440,height:900}});
  const errors=[],assets=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('requestfailed',r=>errors.push(`${r.url()}: ${r.failure()?.errorText}`));
  page.on('response',r=>{
    if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);
    if(/ararat\.glb|navigation\.json|CaveatBrush|rock_boulder_cracked_Diffuse/.test(r.url()))assets.push({url:r.url(),status:r.status()});
  });
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.ararat?.ready&&window.ararat.story?.snapshot.textState==='visible',null,{timeout:240000});
  await page.waitForTimeout(3000);
  const result=await page.evaluate(()=>({title:document.title,stats:window.ararat.stats,story:window.ararat.story.snapshot,fontLoaded:document.fonts.check('36px "Caveat Brush"'),failureVisible:!document.querySelector('#failure').hidden}));
  assert(result.fontLoaded&&!result.failureVisible);
  assert(result.stats.sourceMeshes>3000);
  assert.match(result.story.text,/The water withdrew/);
  for(const name of ['ararat.glb','navigation.json','CaveatBrush','rock_boulder_cracked_Diffuse'])assert(assets.some(a=>a.url.includes(name)&&a.status===200),`${name} must load from the deployed subdirectory`);
  assert.deepEqual(errors,[]);
  await fs.mkdir('artifacts',{recursive:true});
  await page.screenshot({path:'artifacts/deployment.png'});
  await fs.writeFile('artifacts/deployment-verification.json',JSON.stringify({url,...result,assets,errors},null,2));
  console.log(`Deployed exhibition verified: model, navigation, rock texture, handwritten font and opening prose load at ${url}`);
}finally{await browser.close();}
