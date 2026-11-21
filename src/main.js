import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {createNavigation} from './navigation.js';
import {createStory} from './story.js';
import './style.css';

const canvas=document.querySelector('#world');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.setSize(innerWidth,innerHeight);
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.info.autoReset=false;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.22;
const scene=new THREE.Scene();scene.background=new THREE.Color('#9faeb2');
scene.fog=new THREE.FogExp2('#a9bec7',.0038);
const camera=new THREE.PerspectiveCamera(62,innerWidth/innerHeight,.06,600);
camera.position.set(24,2.15,33);camera.lookAt(0,6.4,1);camera.rotation.order='YXZ';
const homeRotation=camera.rotation.clone();
const hemi=new THREE.HemisphereLight('#c0dce8','#39443c',1.7);scene.add(hemi);
const sun=new THREE.DirectionalLight('#fff1cf',2.7);sun.position.set(-20,58,-100);sun.castShadow=true;
const washedFill=new THREE.DirectionalLight('#bdd9e9',.65);washedFill.position.set(30,20,30);scene.add(washedFill);
sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-42,right:42,top:45,bottom:-40,near:1,far:210});
sun.shadow.bias=-.00018;sun.shadow.normalBias=.07;sun.shadow.radius=3;sun.target.position.set(0,0,0);scene.add(sun,sun.target);
const portal=new THREE.PointLight('#ffddae',16,12,2);portal.position.set(3,7,6);scene.add(portal);
const interiorFill=new THREE.PointLight('#d6d8c8',12,16,2);interiorFill.position.set(0,8,-7);scene.add(interiorFill);
const atmosphere={sunset:{value:0},direction:{value:new THREE.Vector3(-20,58,-100).normalize()}};
const boatGroup=new THREE.Group();boatGroup.name='The last boat';scene.add(boatGroup);
let boatInfo=null,story=null;
const coldSun=new THREE.Vector3(-20,58,-100).normalize(),warmSun=new THREE.Vector3(.218,.065,.976).normalize();
const coldFog=new THREE.Color('#a9bec7'),warmFog=new THREE.Color('#a97057'),coldSky=new THREE.Color('#c0dce8'),warmSky=new THREE.Color('#d5a384');
const coldSunColor=new THREE.Color('#fff1cf'),warmSunColor=new THREE.Color('#ffac64'),coldGround=new THREE.Color('#39443c'),warmGround=new THREE.Color('#493544');
function setAtmosphere(t,heading=null,origin=null){
  atmosphere.sunset.value=t;
  if(heading)warmSun.set(heading.x,.065,heading.z).normalize();
  atmosphere.direction.value.lerpVectors(coldSun,warmSun,t).normalize();
  sun.target.position.copy(origin||new THREE.Vector3());sun.position.copy(sun.target.position).addScaledVector(atmosphere.direction.value,120);
  sun.color.lerpColors(coldSunColor,warmSunColor,t);sun.intensity=2.7+t*.4;
  hemi.color.lerpColors(coldSky,warmSky,t);hemi.groundColor.lerpColors(coldGround,warmGround,t);hemi.intensity=1.7-t*.4;
  scene.fog.color.lerpColors(coldFog,warmFog,t);scene.fog.density=.0038-t*.0012;
  renderer.toneMappingExposure=1.22-t*.12;
  bloom.strength=.15+t*.12;
  if(audio&&musicGain)musicGain.gain.setTargetAtTime(t*.026,audio.currentTime,.8);
}

// A painted sky made of slow, layered storm clouds; no screen-space text.
const sky=new THREE.Mesh(new THREE.SphereGeometry(450,48,24),new THREE.ShaderMaterial({
  side:THREE.BackSide,depthWrite:false,uniforms:{time:{value:0},sunset:atmosphere.sunset,sunDirection:atmosphere.direction},
  vertexShader:`varying vec3 v; void main(){v=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader:`varying vec3 v;uniform float time;uniform float sunset;uniform vec3 sunDirection;
  float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
  float fb(vec2 p){return n(p)*.52+n(p*2.03)*.26+n(p*4.09)*.13+n(p*8.1)*.06;}
  void main(){vec3 d=normalize(v);float h=max(0.,d.y);vec3 sd=normalize(sunDirection);float alignment=max(0.,dot(d,sd));
  vec3 c=mix(vec3(.48,.61,.68),vec3(.075,.15,.23),pow(h,.62));
  vec2 q=d.xz/(h+.16)*3.4+vec2(time*.001,0);q+=vec2(fb(q*.67),fb(q*.67+3.))*.8;
  float cloud=fb(q),fine=fb(q*2.7);float opening=pow(alignment,80.);
  float density=smoothstep(.30,.62,cloud)*smoothstep(.015,.15,h)*(1.-opening*.88);
  vec3 cloudColor=mix(vec3(.075,.13,.19),vec3(.40,.48,.53),smoothstep(.31,.63,cloud));
  cloudColor+=vec3(.17,.18,.16)*pow(alignment,19.)*fine;
  c=mix(c,cloudColor,density*.94);c+=vec3(.5,.49,.39)*opening;
  c+=vec3(4.1,3.8,3.1)*pow(alignment,7000.);
  vec3 dusk=mix(vec3(.77,.24,.075),vec3(.11,.075,.14),smoothstep(0.,.62,h));
  dusk+=vec3(.7,.22,.035)*pow(alignment,17.);dusk+=vec3(8.,3.2,.7)*smoothstep(.99983,.99994,alignment);
  dusk=mix(dusk,dusk*.59+vec3(.12,.055,.055),density*.50);
  c=mix(c,dusk,sunset);gl_FragColor=vec4(c,1.);}`
}));scene.add(sky);
const water=new THREE.Mesh(new THREE.PlaneGeometry(1200,1200,1,1),new THREE.ShaderMaterial({
  transparent:false,uniforms:{time:{value:0},fogColor:{value:scene.fog.color},sunset:atmosphere.sunset,sunDirection:atmosphere.direction},
  vertexShader:`varying vec3 w;void main(){w=(modelMatrix*vec4(position,1.)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(w,1.);}`,
  fragmentShader:`varying vec3 w;uniform float time;uniform vec3 fogColor;uniform float sunset;uniform vec3 sunDirection;
  void main(){float ripple=sin(w.x*2.4+w.z*1.7+time*.7)*sin(w.z*.8-time*.25);float r=sin(w.z*4.+sin(w.x*.21)*3.+sin(w.z*.31)*2.+time)*.5+.5;
  vec3 c=mix(vec3(.16,.23,.25),vec3(.42,.46,.43),r*.12+ripple*.035);
  vec2 sunward=normalize(sunDirection.xz),relative=w.xz-cameraPosition.xz;float along=dot(relative,sunward),across=dot(relative,vec2(-sunward.y,sunward.x));
  float width=1.2+max(0.,along)*.065;float pillar=exp(-across*across/(width*width))*smoothstep(1.,12.,along);
  float glint=pow(.5+.5*sin(w.z*8.3+w.x*2.1+sin(w.x*.6+time)*1.8+time*1.1),5.);
  vec3 dusk=mix(vec3(.055,.072,.095),vec3(.25,.13,.075),clamp(along/260.,0.,1.));
  dusk+=vec3(2.4,.91,.13)*pillar*(.12+glint*.88)*( .8+.2*sin(w.x*17.+w.z*12.) );
  c=mix(c,dusk,sunset);float dist=length(w-cameraPosition);c=mix(c,fogColor,1.-exp(-dist*.004));gl_FragColor=vec4(c,1.);}`
}));water.rotation.x=-Math.PI/2;water.position.set(0,-.79,90);scene.add(water);
const reflectionScene=new THREE.Scene();reflectionScene.add(sky.clone());
const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(reflectionScene,.07,.1,500).texture;scene.environmentIntensity=.42;pmrem.dispose();

const composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
const bloom=new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),.15,.55,1.25);composer.addPass(bloom);
const grade=new ShaderPass({uniforms:{tDiffuse:{value:null},time:{value:0}},vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
fragmentShader:`uniform sampler2D tDiffuse;uniform float time;varying vec2 vUv;void main(){vec3 c=texture2D(tDiffuse,vUv).rgb;vec2 p=vUv-.5;float vignette=1.-dot(p,p)*.55;c*=vignette;float grain=fract(sin(dot(vUv+fract(time),vec2(12.9898,78.233)))*43758.5453)-.5;c+=grain*.0035;gl_FragColor=vec4(c,1.);}`});composer.addPass(grade);composer.addPass(new OutputPass());

let loaded=false, locked=false, elapsed=0, audio, musicGain,lastStep=0, focus=null,navigation=null;
const keys=new Set(), direction=new THREE.Vector3(), right=new THREE.Vector3(), velocity=new THREE.Vector3();
let yaw=camera.rotation.y,pitch=camera.rotation.x;
const plantUniforms={time:{value:0}};
const assetUrl=path=>`${import.meta.env.BASE_URL}${path}`;
const rockDetail=new THREE.TextureLoader().load(assetUrl('assets/pbr/rock_boulder_cracked_Diffuse.jpg'));rockDetail.colorSpace=THREE.SRGBColorSpace;rockDetail.wrapS=rockDetail.wrapT=THREE.RepeatWrapping;
const raycaster=new THREE.Raycaster();let solids=[];let stats={};
const rippleData=new Uint8Array(128*128*4);
for(let y=0;y<128;y++)for(let x=0;x<128;x++){
  const i=(y*128+x)*4;const nx=Math.sin(x*.35+y*.12)*.13,ny=Math.cos(y*.31+x*.17)*.13;
  rippleData[i]=(nx*.5+.5)*255;rippleData[i+1]=(ny*.5+.5)*255;rippleData[i+2]=252;rippleData[i+3]=255;
}
const rippleNormal=new THREE.DataTexture(rippleData,128,128);rippleNormal.wrapS=rippleNormal.wrapT=THREE.RepeatWrapping;rippleNormal.magFilter=THREE.LinearFilter;rippleNormal.minFilter=THREE.LinearMipmapLinearFilter;rippleNormal.generateMipmaps=true;rippleNormal.needsUpdate=true;
const ground=(x,z)=>{let y=-z;return .14*Math.sin(x*.23)*Math.cos(y*.15)+.09*Math.cos(y*.4)+.005*(y+15)-Math.max(0,-y-26)*.07-Math.max(0,-x-22)*.045;};
function floorAt(x,z){
  if(navigation)return navigation.heightAt(x,z);
  if(x>=4.65&&x<=15.3&&z>=4.76&&z<=7.24)return .18+(15-x)*.47+.11;
  if(Math.abs(x)<4.95&&Math.abs(z)<19.6)return 4.97;
  return ground(x,z);
}
function canMove(x,z){
  if(x<-30||x>39||z<-31||z>39)return false;
  if(navigation?.surfaceAt(x,z).kind==='ground'&&ground(x,z)<-.97)return false;
  if(Math.abs(floorAt(x,z)-floorAt(camera.position.x,camera.position.z))>.38)return false;
  if(navigation){
    const from=navigation.surfaceAt(camera.position.x,camera.position.z),to=navigation.surfaceAt(x,z);
    if(from.kind!=='ground'&&to.kind==='ground'&&from.height-ground(camera.position.x,camera.position.z)>.4)return false;
  }
  const delta=new THREE.Vector3(x-camera.position.x,0,z-camera.position.z),len=delta.length();
  if(len>.0001){
    raycaster.set(new THREE.Vector3(camera.position.x,camera.position.y-.5,camera.position.z),delta.normalize());raycaster.far=len+.24;
    if(raycaster.intersectObjects(solids,false).length)return false;
  }
  return true;
}
async function load(){
  try{
    const [gltf,nav]=await Promise.all([new GLTFLoader().loadAsync(assetUrl('assets/ararat.glb')),fetch(assetUrl('assets/navigation.json')).then(r=>{if(!r.ok)throw new Error('Navigation surface data is missing');return r.json();})]);
    navigation=createNavigation(nav,ground);
    boatInfo=nav.boat;
    if(!boatInfo)throw new Error('The shore boat is missing from the scene');
    boatGroup.position.fromArray(boatInfo.position);
    gltf.scene.updateMatrixWorld(true);
    const batches=new Map(),roofMaterials=new Map();let triangles=0,original=0;
    gltf.scene.traverse(o=>{
      if(!o.isMesh||o.name.startsWith('Receding_flood_sea'))return;
      const isBoat=o.name.startsWith('Exile');
      const isRoof=/fitted[_ ]roof[_ ]weatherboard|roof[_ ]seam[_ ]batten/.test(o.name);
      original++;const g=o.geometry.clone().applyMatrix4(o.matrixWorld);triangles+=(g.index?.count||g.attributes.position.count)/3;
      if(isBoat)g.translate(-boatInfo.position[0],-boatInfo.position[1],-boatInfo.position[2]);
      // Exported objects remain individually named in Blender; the browser batches by material.
      let m=o.material;
      if(isRoof){
        if(!roofMaterials.has(m.uuid)){
          const roofMat=m.clone();roofMat.normalMap=null;roofMat.bumpMap=null;
          roofMaterials.set(m.uuid,roofMat);
        }
        m=roofMaterials.get(m.uuid);
      }
      m.side=THREE.DoubleSide;m.shadowSide=THREE.FrontSide;
      // The Blender exporter can mistake a Bump input image for a tangent normal.
      // Keep the original height image as a height map instead of misreading brown RGB as XYZ.
      if(!isRoof&&(m.name.startsWith('Cedar')||m.name.startsWith('First earth'))&&!m.normalMap&&m.map){m.bumpMap=m.map;m.bumpScale=m.name.startsWith('First earth')?.035:.004;}
      if(m.name.startsWith('Cedar')){
        m.envMapIntensity=.18;
        m.onBeforeCompile=shader=>{
          shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 woodPosition;').replace('#include <begin_vertex>','#include <begin_vertex>\nwoodPosition=(modelMatrix*vec4(position,1.)).xyz;');
          shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 woodPosition;').replace('#include <map_fragment>','#include <map_fragment>\nfloat enclosed=(1.-smoothstep(4.,5.1,abs(woodPosition.x)))*(1.-smoothstep(18.,22.,abs(woodPosition.z)))*smoothstep(3.9,4.7,woodPosition.y);diffuseColor.rgb*=mix(.48,1.,smoothstep(1.2,4.5,woodPosition.y))*mix(1.,.55,enclosed);').replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=max(.78,roughnessFactor);').replace('#include <lights_fragment_end>','#include <lights_fragment_end>\nreflectedLight.indirectDiffuse*=mix(1.,.26,enclosed);reflectedLight.indirectSpecular*=mix(1.,.4,enclosed);');
        };
      }
      if(m.map){m.map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());}
      if(m.name.startsWith('Boat'))m.envMapIntensity=.3;
      if(m.name.startsWith('Basalt'))m.color.setRGB(.28,.36,.43);
      if(m.name.startsWith('Mountain')){
        m.bumpMap=rockDetail;m.bumpScale=.22;
        m.onBeforeCompile=shader=>{
          shader.uniforms.rockDetail={value:rockDetail};
          shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 mountainPosition;varying vec3 mountainNormal;').replace('#include <begin_vertex>','#include <begin_vertex>\nmountainPosition=(modelMatrix*vec4(position,1.)).xyz;mountainNormal=normalize(mat3(modelMatrix)*normal);');
          shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nuniform sampler2D rockDetail;varying vec3 mountainPosition;varying vec3 mountainNormal;').replace('#include <map_fragment>',`vec3 weights=pow(abs(normalize(mountainNormal)),vec3(5.));weights/=weights.x+weights.y+weights.z;vec3 tx=texture2D(rockDetail,mountainPosition.yz*.16).rgb;vec3 ty=texture2D(rockDetail,mountainPosition.xz*.16).rgb;vec3 tz=texture2D(rockDetail,mountainPosition.xy*.16).rgb;vec3 stoneDetail=tx*weights.x+ty*weights.y+tz*weights.z;diffuseColor.rgb*=.55+stoneDetail*.95;`).replace('#include <fog_fragment>','#include <fog_fragment>\nfloat valleyMist=exp(-max(0.,mountainPosition.y)*.11)*smoothstep(25.,110.,length(mountainPosition-cameraPosition))*.38;gl_FragColor.rgb=mix(gl_FragColor.rgb,vec3(.50,.62,.68),valleyMist);');
        };
      }
      if(m.name.startsWith('Vegetation')&&!m.name.includes('moss')){
        m.onBeforeCompile=shader=>{
          shader.uniforms.windTime=plantUniforms.time;
          shader.vertexShader='uniform float windTime;\n'+shader.vertexShader;
          shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
            float rootY=.14*sin(position.x*.23)*cos(position.z*.15)+.09*cos(position.z*.4)+.005*(-position.z+15.)-max(0.,position.z-26.)*.07-max(0.,-position.x-22.)*.045;
            float tip=smoothstep(.025,.45,position.y-rootY);transformed.x+=sin(windTime*.8+position.x*.9+position.z*.6)*tip*.022;transformed.z+=sin(windTime*.65+position.x*.5)*tip*.012;`);
        };
      }
      if(m.name.startsWith('Puddles')){m.color.setRGB(.09,.14,.16);m.roughness=.08;m.metalness=.05;m.envMapIntensity=1.5;m.normalMap=rippleNormal;m.normalScale.set(.28,.28);}
      if(m.name.startsWith('First earth')){
        m.onBeforeCompile=shader=>{
          shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 soilPosition;').replace('#include <begin_vertex>','#include <begin_vertex>\nsoilPosition=(modelMatrix*vec4(position,1.)).xyz;');
          const noise=`varying vec3 soilPosition;float shash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float sn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(shash(i),shash(i+vec2(1,0)),f.x),mix(shash(i+vec2(0,1)),shash(i+1.),f.x),f.y);}`;
          shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\n'+noise).replace('#include <map_fragment>','#include <map_fragment>\nfloat silt=sn(soilPosition.xz*.16);diffuseColor.rgb*=mix(vec3(.52,.66,.68),vec3(1.12,.97,.78),silt);').replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nfloat wetPocket=smoothstep(.72,.88,sn(soilPosition.xz*.29));roughnessFactor=mix(.84,.34,wetPocket);');
        };
      }
      const k=(isBoat?'boat:':isRoof?'roof:':'world:')+m.uuid;if(!batches.has(k))batches.set(k,{mat:m,geos:[],isBoat,isRoof});batches.get(k).geos.push(g.index?g.toNonIndexed():g);
    });
    for(const {mat,geos,isBoat,isRoof} of batches.values()){
      // Normalize exporter attributes before merging.
      for(const g of geos){for(const name of Object.keys(g.attributes))if(!['position','normal','uv','color'].includes(name))g.deleteAttribute(name);}
      const merged=mergeGeometries(geos,false);if(!merged)throw new Error('Geometry batch failed');
      const mesh=new THREE.Mesh(merged,mat);mesh.castShadow=!['Mountain','First earth','Puddles'].some(p=>mat.name.startsWith(p));mesh.receiveShadow=!isRoof;(isBoat?boatGroup:scene).add(mesh);
      if(!isBoat&&(mat.name.startsWith('Cedar')||mat.name.startsWith('Basalt')||mat.name.startsWith('Unglazed')))solids.push(mesh);
      for(const g of geos)g.dispose();
    }
    stats={triangles,sourceMeshes:original,batches:batches.size,structureRevision:nav.version};
    camera.position.y=floorAt(camera.position.x,camera.position.z)+1.7;camera.lookAt(0,6.4,1);yaw=camera.rotation.y;pitch=camera.rotation.x;loaded=true;
    story=createStory({camera,boat:boatGroup,boatInfo,onPause(){keys.clear();velocity.set(0,0,0);focus=null;if(document.pointerLockElement)document.exitPointerLock();},onResume(){yaw=camera.rotation.y;pitch=camera.rotation.x;},onGesture(){sound();audio?.resume();},onTravel(t,heading){setAtmosphere(t,heading,boatGroup.position);}});
    document.querySelector('#veil').classList.add('open');
    window.dispatchEvent(new Event('ararat-ready'));
  }catch(e){console.error(e);document.querySelector('#failure').hidden=false;}
}
function sound(){
  if(audio)return;audio=new AudioContext();
  // Original synthesized wind and distant water, generated locally after the first gesture.
  const buffer=audio.createBuffer(1,audio.sampleRate*8,audio.sampleRate),a=buffer.getChannelData(0);let brown=0;
  for(let i=0;i<a.length;i++){brown=(brown+(Math.random()*2-1)*.015)/1.015;a[i]=brown*3;}
  const noise=audio.createBufferSource();noise.buffer=buffer;noise.loop=true;
  const filter=audio.createBiquadFilter();filter.type='lowpass';filter.frequency.value=480;
  const gain=audio.createGain();gain.gain.value=.22;noise.connect(filter).connect(gain).connect(audio.destination);noise.start();
  const lfo=audio.createOscillator(),lg=audio.createGain();lfo.frequency.value=.075;lg.gain.value=.08;lfo.connect(lg).connect(gain.gain);lfo.start();
  musicGain=audio.createGain();musicGain.gain.value=0;musicGain.connect(audio.destination);
  for(const [i,freq] of [130.81,196,261.63].entries()){const tone=audio.createOscillator(),level=audio.createGain();tone.type='sine';tone.frequency.value=freq;tone.detune.value=(i-1)*3;level.gain.value=.28;tone.connect(level).connect(musicGain);tone.start();}
}
function footstep(){
  if(!audio)return;const b=audio.createBuffer(1,audio.sampleRate*.16,audio.sampleRate),a=b.getChannelData(0);
  for(let i=0;i<a.length;i++)a[i]=(Math.random()*2-1)*Math.exp(-i/a.length*8)*.12;
  const s=audio.createBufferSource();s.buffer=b;const f=audio.createBiquadFilter();f.type='lowpass';f.frequency.value=camera.position.y>4?300:140;s.connect(f).connect(audio.destination);s.start();
}
canvas.addEventListener('click',()=>{if(!loaded)return;if(story?.canvasClick())return;if(!story?.canWalk)return;sound();audio?.resume();canvas.requestPointerLock?.();});
document.addEventListener('pointerlockchange',()=>{locked=document.pointerLockElement===canvas;if(!locked){keys.clear();velocity.set(0,0,0);}});
document.addEventListener('mousemove',e=>{if(locked&&story?.canWalk){yaw-=e.movementX*.0017;pitch=THREE.MathUtils.clamp(pitch-e.movementY*.0017,-1.3,1.3);}});
document.addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','KeyE'].includes(e.code))e.preventDefault();if(e.repeat&&(e.code==='KeyE'||e.code==='Space'))return;
  if(story?.snapshot.reading){if(['KeyE','Space','Enter'].includes(e.code))story.advance();return;}
  if(e.code==='KeyE'&&story?.tryInteract())return;if(!story?.canWalk)return;
  keys.add(e.code);if(e.code==='KeyE'&&locked){focus=focus?null:nearestFocus();}});
document.addEventListener('keyup',e=>keys.delete(e.code));
window.addEventListener('blur',()=>keys.clear());
function nearestFocus(){let p=new THREE.Vector3(17.1,.8,20);if(camera.position.distanceTo(p)<4)return p;p=new THREE.Vector3(-1.4,6.3,6.2);return camera.position.distanceTo(p)<4?p:null;}

// Slow ash-like water motes, visible only in shafts of light.
const motesGeo=new THREE.BufferGeometry(),motes=[];for(let i=0;i<65;i++)motes.push(Math.random()*8-4,Math.random()*4+5,Math.random()*34-17);
motesGeo.setAttribute('position',new THREE.Float32BufferAttribute(motes,3));const dust=new THREE.Points(motesGeo,new THREE.PointsMaterial({color:'#e2e7dc',size:.012,transparent:true,opacity:.16,depthWrite:false}));scene.add(dust);

let previous=performance.now(),frames=0;
function frame(now){requestAnimationFrame(frame);const dt=Math.min((now-previous)/1000,.04);previous=now;elapsed+=dt;
  sky.material.uniforms.time.value=elapsed;water.material.uniforms.time.value=elapsed;grade.uniforms.time.value=elapsed;dust.position.x=Math.sin(elapsed*.04)*.5;
  rippleNormal.offset.set(elapsed*.006,elapsed*.003);
  plantUniforms.time.value=elapsed;
  sky.position.copy(camera.position);
  const mood=story?.update(dt,elapsed);if(mood&&!mood.travel)setAtmosphere(mood.sunset);
  if(loaded){
    if(locked&&story?.canWalk){
      const forward=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0);
      const strafe=(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0);
      direction.set(-Math.sin(yaw),0,-Math.cos(yaw));right.set(Math.cos(yaw),0,-Math.sin(yaw));
      const desired=direction.multiplyScalar(forward).add(right.multiplyScalar(strafe));if(desired.lengthSq()>0)desired.normalize();
      desired.multiplyScalar(keys.has('ShiftLeft')?3.25:2.1);velocity.lerp(desired,1-Math.exp(-dt*9));
      let x=camera.position.x+velocity.x*dt,z=camera.position.z+velocity.z*dt;
      if(canMove(x,camera.position.z))camera.position.x=x;if(canMove(camera.position.x,z))camera.position.z=z;
      const moving=velocity.length()>.2;const bob=moving?Math.sin(elapsed*9)*.018:Math.sin(elapsed*1.2)*.004;
      camera.position.y=THREE.MathUtils.lerp(camera.position.y,floorAt(camera.position.x,camera.position.z)+1.7+bob,1-Math.exp(-dt*14));
      if(moving&&elapsed-lastStep>.54){footstep();lastStep=elapsed;}
      if(focus){const q=new THREE.Quaternion();const dummy=new THREE.Object3D();dummy.position.copy(camera.position);dummy.lookAt(focus);q.copy(dummy.quaternion);camera.quaternion.slerp(q,1-Math.exp(-dt*4));const e=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');yaw=e.y;pitch=e.x;}
      else camera.rotation.set(pitch,yaw,Math.sin(elapsed*1.1)*.0008,'YXZ');
    }else if(story?.canWalk){
      camera.rotation.set(pitch+Math.sin(elapsed*.19)*.0015,yaw+Math.sin(elapsed*.12)*.002,0,'YXZ');
    }
  }
  renderer.info.reset();composer.render();frames++;
}
requestAnimationFrame(frame);load();
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);});
// A read-only diagnostic snapshot plus an explicit test navigation hook, never rendered as UI.
window.ararat={get ready(){return loaded;},get stats(){return {...stats,drawCalls:renderer.info.render.calls,frames};},get position(){return camera.position.toArray();},get story(){return story;},floorAt,canMove,
  visit(name){const points={arrival:[24,2.15,33,0,6.4,1],olive:[18.3,2.55,22.3,17,.65,20],threshold:[10,floorAt(10,6)+1.7,6,3,6.8,6],interior:[1,6.67,8,-1.4,6.2,6.2],valley:[5,6.67,6,24,1,28],growth:[26.5,1.9,19.2,25,.35,17],mountains:[30,2.1,6,22,36,-80],'stair-foot':[20,1.8,9,11,2.7,6],'stair-side':[14,2.1,13,10,2.5,6],'door-joint':[7.1,6.67,6,4.6,6.4,6],'stair-walk':[17.5,floorAt(17.5,6)+1.7,6,0,6.67,6],stern:[12,2.8,29,0,4.5,20],bow:[12,2.8,-29,0,4.5,-20],roof:[18,14,18,0,10.3,0],exile:[25.1,floorAt(25.1,34.6)+1.7,34.6,26,-.32,39],'exile-wide':[22.4,1.5,35.1,26,-.3,39],'linen-memory':[.7,6.67,7.3,-1.4,6.2,6.2],'rope-memory':[1.7,6.67,7.55,1.7,5.1,10]};const p=points[name];if(!p)return;camera.position.set(...p.slice(0,3));if(name==='arrival')camera.position.y=floorAt(24,33)+1.7;camera.lookAt(...p.slice(3));yaw=camera.rotation.y;pitch=camera.rotation.x;velocity.set(0,0,0);},
  verifyRoute(points){let failures=[];const saved=camera.position.clone();for(const [x,z] of points){const start=camera.position.clone();const steps=Math.ceil(Math.hypot(x-start.x,z-start.z)/.07);for(let i=1;i<=steps;i++){const xx=THREE.MathUtils.lerp(start.x,x,i/steps),zz=THREE.MathUtils.lerp(start.z,z,i/steps);if(!canMove(xx,zz)){failures.push({from:camera.position.toArray(),to:[xx,zz]});break;}camera.position.set(xx,floorAt(xx,zz)+1.7,zz);}}camera.position.copy(saved);return failures;},get locked(){return locked;}};
