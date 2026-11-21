import * as THREE from 'three';

export const STORY = {
  prologue:[
    'The water withdrew.\nThe names did not.',
    'They called this a beginning.\nI called it the place I had not drowned.',
    'Before I could leave the ark behind,\nI had to return to what I had carried ashore.'
  ],
  olive:[
    'An olive branch. No map. No oath.\nOnly something living,\nreturned from a world we could not see.',
    'I had mistaken being spared\nfor being forgiven.'
  ],
  linen:[
    'We wrapped the empty places in linen,\nas if mercy could be folded small enough to carry.',
    'The ark had brought my body to shore.\nThe rest of me was still at sea.'
  ],
  rope:[
    'I tied a knot for each name I was afraid to forget.\nWhen the rope ran out, I kept counting.',
    'Perhaps redemption is not a shore.\nPerhaps it is what we choose not to abandon.'
  ],
  ready:[
    'There was still a little boat at the waterline.\nOne oar. One bundle. Room for one unfinished life.',
    'I had left its last rope loose.'
  ],
  notReady:['I could not leave\nwhile the names were still knotted inside.'],
  departure:[
    'I could stay. I could build a door,\nand call this shore the promised land.',
    'But I would be making a home of a verdict.\nI took one oar. I took the leaf.',
    'I left the last rope untied.'
  ],
  ending:[
    'We never arrived at the promised land.',
    'There was only a world washed clean,\nand a life I had not yet learned to inhabit.',
    'I called it exile.\nFor the first time, it did not feel like drowning.'
  ]
};

export const STORY_TIMING = Object.freeze({
  proseIn:1800,proseOut:1500,pagePause:300,
  afterglow:4.5,fadeToBlack:4.5,blackHold:1.2,fadeFromBlack:4.5
});

export function createStory({camera,boat,boatInfo,onPause,onResume,onGesture,onTravel}){
  const manuscript=document.createElement('section');manuscript.id='manuscript';manuscript.setAttribute('aria-label','A handwritten memory');
  const paper=document.createElement('div');paper.className='story-passage';
  const text=document.createElement('p');text.className='memory-ink';paper.append(text);manuscript.append(paper);document.body.append(manuscript);
  const black=document.createElement('div');black.id='story-black';black.setAttribute('aria-hidden','true');document.body.append(black);
  let phase='prologue',pages=[],pageIndex=0,afterReading=null,reading=false,enabled=true,cooldown=0,departTime=0,epilogueShown=false,earlyBoatShown=false;
  let textState='hidden',textEpoch=0,textTimer=null,afterglowTime=0,returnTime=0,homeReset=false,loopCount=0;
  const homePosition=camera.position.clone(),homeQuaternion=camera.quaternion.clone(),homeFov=camera.fov,homeBoatQuaternion=boat.quaternion.clone();
  const memories=new Set(),origin=new THREE.Vector3(...boatInfo.position),heading=new THREE.Vector3(...boatInfo.heading);
  const stern=new THREE.Vector3(...boatInfo.stern);let cameraStart=new THREE.Vector3(),lookStart=new THREE.Vector3();
  const nodes=[{id:'olive',position:new THREE.Vector3(17,.6,20),radius:2.9},
    {id:'linen',position:new THREE.Vector3(-1.4,6.2,6.2),radius:2.9},
    {id:'rope',position:new THREE.Vector3(1.7,5.05,10),radius:2.6}];
  function near(p,r){return Math.hypot(camera.position.x-p.x,camera.position.z-p.z)<r&&Math.abs(camera.position.y-p.y)<3;}
  function cancelTextTransition(){textEpoch++;clearTimeout(textTimer);textTimer=null;}
  function afterTextDelay(ms,callback){
    const epoch=textEpoch;clearTimeout(textTimer);
    textTimer=setTimeout(()=>{textTimer=null;if(enabled&&epoch===textEpoch)callback();},ms);
  }
  function fadePassageIn(){
    textState='fadingIn';text.textContent=pages[pageIndex];
    manuscript.classList.remove('visible');manuscript.classList.add('reading');manuscript.style.setProperty('--prose-fade',`${STORY_TIMING.proseIn}ms`);
    // Resolve the transparent layout before showing new ink, including the first reading.
    manuscript.getBoundingClientRect();
    const epoch=textEpoch;
    requestAnimationFrame(()=>{
      if(!enabled||epoch!==textEpoch)return;
      manuscript.classList.add('visible');
      afterTextDelay(STORY_TIMING.proseIn,()=>{textState='visible';});
    });
  }
  function show(lines,done){
    cancelTextTransition();
    pages=lines;pageIndex=0;afterReading=done;reading=true;onPause();
    fadePassageIn();
  }
  function advance(){
    if(!reading)return false;
    // Repeated clicks during a dissolve cannot skip text or flash the next passage.
    if(textState!=='visible')return true;
    onGesture();cancelTextTransition();textState='fadingOut';
    manuscript.style.setProperty('--prose-fade',`${STORY_TIMING.proseOut}ms`);manuscript.classList.remove('visible');
    afterTextDelay(STORY_TIMING.proseOut,()=>{
      textState='hidden';text.textContent='';
      if(pageIndex+1<pages.length){
        pageIndex++;afterTextDelay(STORY_TIMING.pagePause,fadePassageIn);return;
      }
      reading=false;manuscript.classList.remove('reading');cooldown=3;
      const done=afterReading;afterReading=null;if(done)done();
      if(phase==='explore'&&!reading)onResume();
    });
    return true;
  }
  paper.addEventListener('click',e=>{e.stopPropagation();advance();});
  function remember(node){
    show(STORY[node.id],()=>{
      memories.add(node.id);phase='explore';
      if(memories.size===3)show(STORY.ready,()=>{phase='explore';});
    });
  }
  function startVoyage(){
    phase='voyage';departTime=0;epilogueShown=false;cameraStart.copy(camera.position);
    camera.getWorldDirection(lookStart);lookStart.multiplyScalar(15).add(camera.position);onPause();
    document.body.classList.add('on-voyage');
  }
  function restoreOpening(){
    cancelTextTransition();reading=false;textState='hidden';text.textContent='';
    manuscript.classList.remove('visible','reading');
    memories.clear();earlyBoatShown=false;epilogueShown=false;cooldown=0;departTime=0;
    pages=[];pageIndex=0;afterReading=null;
    boat.position.copy(origin);boat.quaternion.copy(homeBoatQuaternion);
    camera.position.copy(homePosition);camera.quaternion.copy(homeQuaternion);camera.fov=homeFov;camera.updateProjectionMatrix();
    document.body.classList.remove('on-voyage');onTravel(0,heading);onResume();homeReset=true;
  }
  function tryInteract(){
    if(!enabled)return false;
    if(reading)return advance();
    if(phase!=='explore')return true;
    for(const node of nodes){if(!memories.has(node.id)&&near(node.position,node.radius)){remember(node);return true;}}
    if(near(stern,3.0)){
      if(memories.size===3){show(STORY.departure,startVoyage);return true;}
      show(STORY.notReady,()=>{phase='explore';});earlyBoatShown=true;return true;
    }
    return false;
  }
  function update(dt,time){
    if(!enabled)return {sunset:0,travel:false};
    cooldown=Math.max(0,cooldown-dt);
    if(phase==='explore'&&!reading&&cooldown===0){
      const forward=new THREE.Vector3();camera.getWorldDirection(forward);
      for(const node of nodes){
        if(!memories.has(node.id)&&near(node.position,1.9)){
          const direction=node.position.clone().sub(camera.position).normalize();
          if(direction.dot(forward)>.1){remember(node);break;}
        }
      }
      if(!reading&&near(stern,1.8)&&memories.size===3)show(STORY.departure,startVoyage);
      else if(!reading&&!earlyBoatShown&&near(stern,1.8)){show(STORY.notReady,()=>{phase='explore';});earlyBoatShown=true;}
    }
    if(phase==='afloat'){
      afterglowTime+=dt;
      if(afterglowTime>=STORY_TIMING.afterglow){phase='returning';returnTime=0;homeReset=false;onPause();}
    }
    if(phase==='returning'){
      returnTime+=dt;
      const fadeOutEnd=STORY_TIMING.fadeToBlack,holdEnd=fadeOutEnd+STORY_TIMING.blackHold,total=holdEnd+STORY_TIMING.fadeFromBlack;
      if(returnTime>=fadeOutEnd&&!homeReset)restoreOpening();
      const opacity=returnTime<fadeOutEnd?THREE.MathUtils.smootherstep(returnTime,0,fadeOutEnd):returnTime<holdEnd?1:1-THREE.MathUtils.smootherstep(returnTime,holdEnd,total);
      black.style.opacity=String(opacity);
      if(returnTime>=total){
        black.style.opacity='0';phase='prologue';loopCount++;
        show(STORY.prologue,()=>{phase='explore';});
      }
      return {sunset:homeReset?0:1,travel:!homeReset};
    }
    if(phase==='voyage'||phase==='afloat'){
      departTime+=dt;
      const boarding=THREE.MathUtils.smootherstep(departTime,0,4.2);
      const sailing=Math.max(0,departTime-4.2),distance=Math.min(115,sailing*1.25);
      boat.position.copy(origin).addScaledVector(heading,distance);
      boat.position.y=Math.sin(time*1.25)*.018;
      boat.rotation.z=Math.sin(time*.65)*.008;
      const seat=boat.position.clone().addScaledVector(heading,-.85);seat.y=boatInfo.floorLevel+1.03+boat.position.y;
      const destination=boat.position.clone().addScaledVector(heading,80);destination.y=boatInfo.waterLevel+6.3;
      camera.position.lerpVectors(cameraStart,seat,boarding);
      camera.lookAt(lookStart.clone().lerp(destination,boarding));
      camera.fov=THREE.MathUtils.lerp(62,56,boarding);camera.updateProjectionMatrix();
      const sunset=THREE.MathUtils.smootherstep(sailing,0,18);
      black.style.opacity=departTime<2?String(Math.sin(departTime/2*Math.PI)*.85):'0';
      onTravel(sunset,heading);
      if(sailing>30&&!epilogueShown){epilogueShown=true;show(STORY.ending,()=>{phase='afloat';afterglowTime=0;});}
      return {sunset,travel:true};
    }
    return {sunset:memories.size===3?.045:0,travel:false};
  }
  // The local font is loaded before ink is shown; a system UI font never flashes on screen.
  document.fonts.load('36px "Caveat Brush"').then(()=>{
    if(enabled&&phase==='prologue')show(STORY.prologue,()=>{phase='explore';});
  });
  return {
    get canWalk(){return !enabled||(phase==='explore'&&!reading);},
    get cameraDriven(){return enabled&&(phase==='voyage'||phase==='afloat'||phase==='returning');},
    get snapshot(){return {phase,reading,text:text.textContent,textState,pageIndex,memories:[...memories],voyageTime:departTime,boatPosition:boat.position.toArray(),blackOpacity:Number(black.style.opacity)||0,homeReset,loopCount,homePosition:homePosition.toArray()};},
    advance,tryInteract,update,
    canvasClick(){return reading?advance():false;},
    disableForTesting(){cancelTextTransition();enabled=false;reading=false;textState='hidden';text.textContent='';manuscript.classList.remove('visible','reading');black.style.opacity='0';phase='explore';onResume();},
    setVoyageTimeForTesting(t){if(phase==='voyage'||phase==='afloat')departTime=t;}
  };
}
