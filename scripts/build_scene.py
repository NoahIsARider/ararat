import bpy, math, random, os, json
from mathutils import Vector
from mathutils.noise import noise_vector
random.seed(74)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'assets')
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, 'blender'), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection' and c.users == 0: bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
groups={}
for name in ['01_Ark', '02_Interior', '03_Shore', '04_Mountains', '05_Olive', '06_Lighting', '07_Collision', '08_First_Growth']:
    c=bpy.data.collections.new(name); scene.collection.children.link(c); groups[name]=c
def group(o,g):
    for c in list(o.users_collection): c.objects.unlink(o)
    groups[g].objects.link(o)
    return o
def material(name,col,rough=.7):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*col,1); p.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*col,1)
    return m
def texture(name,w,h,kind):
    im=bpy.data.images.new(name,width=w,height=h); pixels=[]
    for y in range(h):
        for x in range(w):
            u=x/w; v=y/h
            if kind=='wood':
                flow=v*65+math.sin(u*9+v*4)*.22+math.sin(u*21)*.07
                grain=(math.sin(flow*math.pi*2)*.5+.5)**12
                fine=(math.sin(flow*7+u*31)*.5+.5)*.025
                knot=math.exp(-((u-.32)**2*140+(v-.47)**2*250))
                ring=math.sin(math.sqrt((u-.32)**2*10+(v-.47)**2*3)*160)**10*knot
                value=.59+.035*math.sin(v*21)+random.random()*.025-grain*.065-fine-ring*.10
                weather=.025*math.sin(u*2+v*6)
                pixels.extend((value*.36+weather,value*.30+weather,value*.23+weather,1))
            else:
                n=noise_vector(Vector((u*19,v*19,2))).x
                s=noise_vector(Vector((u*90,v*90,0))).x
                value=.46+n*.22+s*.06+random.random()*.035
                pixels.extend((value*.55,value*.43,value*.31,1))
    im.pixels.foreach_set(pixels); im.filepath_raw=os.path.join(OUT,name+'.png'); im.file_format='PNG'; im.save(); im.pack()
    return im
woodim=texture('Cedar_hand_hewn_grain',1024,256,'wood')
soilIm=texture('First_silt_ochre_ash',512,512,'soil')
woods=[]
for i in range(5):
    m=material('Cedar | grain %02d'%i,(.2,.1,.04),.65+i*.035)
    n=m.node_tree.nodes; l=m.node_tree.links; p=next(n for n in n if n.type=='BSDF_PRINCIPLED')
    t=n.new('ShaderNodeTexImage'); t.image=woodim
    l.new(t.outputs['Color'],p.inputs['Base Color'])
    b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.32; b.inputs['Distance'].default_value=.055
    l.new(t.outputs['Color'],b.inputs['Height']); l.new(b.outputs[0],p.inputs['Normal'])
    woods.append(m)
soil=material('First earth | saturated ochre and silt',(.18,.13,.08),.82)
t=soil.node_tree.nodes.new('ShaderNodeTexImage');t.image=soilIm
p=next(n for n in soil.node_tree.nodes if n.type=='BSDF_PRINCIPLED'); soil.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
b=soil.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.3;b.inputs['Distance'].default_value=.13
soil.node_tree.links.new(t.outputs['Color'],b.inputs['Height']);soil.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
rock=material('Basalt | river polished',(.065,.079,.075),.87)
dark=material('Pitch | caulk',(.032,.026,.02),.75)
rope=material('Flax | weathered rope',(.31,.25,.16),.93)
leaf=material('Olive | silver green',(.065,.14,.045),.58)
leaf2=material('Olive | pale underside',(.17,.23,.12),.72)
cloth=material('Unbleached linen',(.48,.39,.25),.98)
wet=material('Puddles | suspended silt',(.045,.07,.075),.16)
def scanned_pbr(materials,asset_id):
    folder=os.path.join(OUT,'pbr')
    imgs={}
    for key in ['Diffuse','nor_gl','Rough']:
        path=os.path.join(folder,asset_id+'_'+key+'.jpg')
        if not os.path.isfile(path):return
        img=bpy.data.images.load(path,check_existing=True)
        if key!='Diffuse':img.colorspace_settings.name='Non-Color'
        img.pack();imgs[key]=img
    for m in materials:
        nodes=m.node_tree.nodes;links=m.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        for socket in ['Base Color','Normal','Roughness']:
            for l in list(p.inputs[socket].links):links.remove(l)
        tx={}
        for key in imgs:
            tx[key]=nodes.new('ShaderNodeTexImage');tx[key].image=imgs[key]
        if asset_id=='rock_boulder_cracked':
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
            mix.inputs[2].default_value=(.28,.36,.43,1)
            links.new(tx['Diffuse'].outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],p.inputs['Base Color'])
        else:links.new(tx['Diffuse'].outputs['Color'],p.inputs['Base Color'])
        links.new(tx['Rough'].outputs['Color'],p.inputs['Roughness'])
        nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.62
        links.new(tx['nor_gl'].outputs['Color'],nm.inputs['Color']);links.new(nm.outputs[0],p.inputs['Normal'])
scanned_pbr(woods,'rough_wood')
scanned_pbr([soil],'brown_mud_03')
scanned_pbr([rock],'rock_boulder_cracked')
def mesh(name,vs,fs,mat,g='03_Shore',uv=None):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    o=bpy.data.objects.new(name,me);groups[g].objects.link(o);o.data.materials.append(mat)
    layer=me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi=me.loops[li].vertex_index
            if uv: layer.data[li].uv=uv[vi]
            else:
                v=vs[vi];layer.data[li].uv=(v[0]*.12,v[1]*.12)
    return o
def box(name,loc,scale,mat,g='01_Ark',bevel=.04):
    sx,sy,sz=[s*.5 for s in scale]
    vs=[(-sx,-sy,-sz),(-sx,-sy,sz),(-sx,sy,-sz),(-sx,sy,sz),(sx,-sy,-sz),(sx,-sy,sz),(sx,sy,-sz),(sx,sy,sz)]
    fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o=mesh(name,vs,fs,mat,g);o.location=loc
    # UV length follows the long axis; grain runs the length of each board.
    axis=max(range(3),key=lambda a:scale[a]);other=0 if axis!=0 else 1
    if o.data.uv_layers:
        for lp in o.data.loops:
            co=o.data.vertices[lp.vertex_index].co
            o.data.uv_layers.active.data[lp.index].uv=(co[axis]/max(scale[axis],.01)+.5,co[other]/max(scale[other],.01)+.5)
    if bevel:
        mod=o.modifiers.new('Worn arris', 'BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def line(name,points,r,mat,g='01_Ark'):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,cu);groups[g].objects.link(o);cu.materials.append(mat);return o
def beam(name,a,b,r,mat,g='01_Ark'):
    a=Vector(a);b=Vector(b);o=box(name,(a+b)/2,(r,r,(b-a).length),mat,g,.025)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
stone_template=None
def stone(name,pos,size,g='03_Shore'):
    global stone_template
    if stone_template is None:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
        temp=bpy.context.object;stone_template=([v.co.copy() for v in temp.data.vertices],[tuple(p.vertices) for p in temp.data.polygons]);bpy.data.objects.remove(temp,do_unlink=True)
    vs=[tuple(v*random.uniform(.86,1.15)) for v in stone_template[0]]
    o=mesh(name,vs,stone_template[1],rock,g);o.location=pos
    # Spherical UVs avoid stretching a top projection down vertical rock faces.
    uv=o.data.uv_layers.active
    for poly in o.data.polygons:
        values=[]
        for idx in poly.loop_indices:
            co=o.data.vertices[o.data.loops[idx].vertex_index].co
            values.append((idx,math.atan2(co.y,co.x)/math.tau+.5,math.asin(max(-1,min(1,co.z/co.length)))/math.pi+.5))
        seam=max(v[1] for v in values)-min(v[1] for v in values)>.5
        for idx,u,v in values:uv.data[idx].uv=(u+1 if seam and u<.5 else u,v)
    o.scale=size;o.rotation_euler=(random.random(),random.random(),random.random()*6)
    for p in o.data.polygons:p.use_smooth=True
    return o
def height(x,y):
    return .14*math.sin(x*.23)*math.cos(y*.15)+.09*math.cos(y*.4)+.005*(y+15)-max(0,-y-26)*.07-max(0,-x-22)*.045
N=115;vs=[];uv=[]
for j in range(N):
    y=-65+j*1.5
    for i in range(N):
        x=-80+i*1.5;vs.append((x,y,height(x,y)));uv.append((x*.22,y*.22))
fs=[]
for j in range(N-1):
    for i in range(N-1):
        a=j*N+i;fs.append((a,a+1,a+N+1,a+N))
terrain=mesh('Exposed flood sediment',vs,fs,soil,uv=uv)
for p in terrain.data.polygons:p.use_smooth=True
# The same module is used for a full build and for incremental ark-only revisions.
exec(compile(open(os.path.join(ROOT,'scripts','ark_structure.py'),encoding='utf-8').read(),'ark_structure.py','exec'),globals())
# Long voyage objects: clay jars, loose rope coils, crates, nets, animal partitions.
def jar(pos,s=1):
    profile=[(.28,0),(.47,.15),(.53,.65),(.45,.95),(.24,1.1),(.24,1.25),(.19,1.25),(.18,1.1)]
    vs=[];fs=[]
    for r,z in profile:
        for k in range(32):vs.append((pos[0]+math.cos(k*math.tau/32)*r*s,pos[1]+math.sin(k*math.tau/32)*r*s,pos[2]+z*s))
    for j in range(len(profile)-1):
        for k in range(32):a=j*32+k;b=j*32+(k+1)%32;fs.append((a,b,b+32,a+32))
    o=mesh('Clay water vessel',vs,fs,clay,'02_Interior')
    for p in o.data.polygons:p.use_smooth=True
clay=material('Unglazed clay',(.34,.18,.09),.95)
for pos in [(-3,-14,4.97),(-2,-14.6,4.97),(3,5,4.97),(-3,10,4.97)]:jar(pos,random.uniform(.7,1.2))
for i in range(5):
    pts=[]
    for k in range(160):
        t=k/159*math.tau*4;r=.28+t*.007
        pts.append((1.7+r*math.cos(t),-10+r*math.sin(t),5.01+i*.045))
    line('Coiled voyage rope',pts,.025,rope,'02_Interior')
# A quiet offering table, linen and an olive cutting. No typeset text.
for x in [-2.2,-.6]:
    for y in [-6.7,-5.7]:box('Table pegged leg',(x,y,5.5),(.12,.12,1.1),woods[0],'02_Interior')
for i in range(5):box('Offering table top',(-1.4,-6.2+i*.24-.48,6.07),(2.1,.23,.12),woods[1],'02_Interior')
# Stowed voyage provisions, folded linen and an empty feeding trough.
for x,y in [(-3.0,-10),(2.8,12),(-2.35,16)]:
    for lev in range(2):
        for k in range(5):
            box('Provision chest slat',(x,y-.5+k*.25,5.15+lev*.65),(1.25,.23,.12),woods[(k+lev)%5],'02_Interior')
        for xx in [x-.57,x+.57]:box('Provision chest end',(xx,y,5.42+lev*.65),(.12,1.25,.55),woods[2],'02_Interior')
        for yy in [y-.57,y+.57]:box('Provision chest side',(x,yy,5.42+lev*.65),(1.15,.12,.55),woods[1],'02_Interior')
for i in range(4):
    o=box('Folded storm linen',(-2.9,-10,6.52+i*.055),(1.1,.85,.05),cloth,'02_Interior',.04);o.rotation_euler[2]=.04*math.sin(i*2)
for x in [-2.9,2.9]:
    box('Empty feeding trough bottom',(x,2,5.15),(1.7,.65,.17),woods[4],'02_Interior')
    for yy in [1.65,2.35]:box('Trough worn lip',(x,yy,5.42),(1.8,.11,.5),woods[3],'02_Interior')
    for xx in [x-.85,x+.85]:box('Trough end',(xx,2,5.42),(.12,.65,.5),woods[3],'02_Interior')
v=[]
for j in range(12):
    for i in range(15):
        x=-2.25+i*.12;y=-6.7+j*.09;z=6.15+.015*math.sin(i*1.7+j*.7)
        v.append((x,y,z))
linen=mesh('Crinkled linen',v,[(j*15+i,j*15+i+1,(j+1)*15+i+1,(j+1)*15+i) for j in range(11) for i in range(14)],cloth,'02_Interior')
for poly in linen.data.polygons:poly.use_smooth=True
def olive(origin,scale=1):
    ox,oy,oz=origin
    def P(x,y,z):return (ox+x*scale,oy+y*scale,oz+z*scale)
    line('Olive | supple woody stem',[P(i*.11,math.sin(i*.28)*.08,i*.012) for i in range(14)],.016*scale,woods[1],'05_Olive')
    for i in range(2,13):
        for side in [-1,1]:
            x=i*.11;y=math.sin(i*.28)*.08
            a=P(x,y,i*.012);end=P(x+.07,y+side*random.uniform(.14,.19),i*.012+.045)
            center=Vector(end);axis=Vector((.10+random.uniform(-.03,.05),side*.26,.025))*scale;cross=Vector((-.033*side,.014,.012))*scale
            line('Olive | leaf petiole',[a,tuple(center-axis*.5)],.003*scale,woods[0],'05_Olive')
            verts=[]
            for k in range(13):
                t=k/12;mid=center+axis*(t-.5)+Vector((0,0,math.sin(t*math.pi)*.015*scale))
                w=math.sin(t*math.pi)**.8
                verts.extend([tuple(mid-cross*w),tuple(mid+cross*w)])
            faces=[(k*2,k*2+1,k*2+3,k*2+2) for k in range(12)]
            o=mesh('Olive | lanceolate leaf',verts,faces,leaf if i%3 else leaf2,'05_Olive')
            for poly in o.data.polygons:poly.use_smooth=True
            so=o.modifiers.new('Leaf thickness','SOLIDIFY');so.thickness=.001
            line('Olive | silver midrib',[tuple(center+axis*(t-.5)+Vector((0,0,.016*scale*math.sin(t*math.pi)))) for t in [k/12 for k in range(13)]],.0008*scale,leaf2,'05_Olive')
olive((-2,-6.4,6.2),1)
# Foreground rock and branch create a reachable first narrative node.
offering=stone('Shore offering stone',(17,-20,.22),(1.5,.9,.38));offering.rotation_euler=(0,0,0)
# A deliberately fixed flat top prevents stochastic rocks from swallowing the hero branch.
for vert in offering.data.vertices:
    if vert.co.z>.25:vert.co.z=.80
olive((16.4,-20.1,.22+.38*.80+.045),1.1)
# The grounded keel rests on a rough ridge, with visible compression/contact shadows.
for y in [-17,-8,2,12,18]:
    o=stone('Keel grounding ridge',(0,y,.1),(3.1,3.7,1.1));o.rotation_euler=(0,0,random.random())
for x in [-2.7,2.7]:
    for y in [-12,7]:
        o=stone('Hull contact boulder',(x,y,.3),(1.35,2.3,.95));o.rotation_euler=(0,0,random.random())
# Flood trace: embedded stones, debris, silt ripples, footprints and shallow pools.
for i in range(210):
    x=random.uniform(-36,38);y=random.uniform(-37,35)
    if abs(x)<6.5 and abs(y)<23:continue
    if 4<x<16 and -8<y<-4:continue
    s=random.uniform(.07,.6);stone('Water worn shore stone',(x,y,height(x,y)+s*.15),(s*1.6,s,s*.65))
for i in range(24):
    x=random.uniform(-25,30);y=random.uniform(-30,26)
    if abs(x)<8 and abs(y)<23:continue
    pts=[(x+k*.18,y+math.sin(k*.3)*.1,height(x+k*.18,y)+.08) for k in range(random.randint(6,18))]
    line('Flood driftwood',pts,random.uniform(.025,.09),woods[3],'03_Shore')
# One shattered trunk frames the abandoned shore; all limbs are modelled curves.
trunk=(-10,-22,height(-10,-22))
line('Storm broken trunk',[trunk,(-10.2,-21.9,1.3),(-10.5,-21.5,2.7),(-10.1,-21.3,4.1)],.16,woods[4],'03_Shore')
for i in range(9):
    z=1+i*.29;side=1 if i%2 else -1
    start=(-10.2,-21.7,z);tip=(-10.2+side*(1.1+random.random()),-21.8+random.uniform(-.8,.8),z+.8)
    line('Storm splintered limb',[start,((start[0]+tip[0])*.5,tip[1],z+.2),tip],.035,woods[4],'03_Shore')
    line('Broken twig',[tip,(tip[0]+side*.35,tip[1]+.18,tip[2]+.4)],.012,woods[3],'03_Shore')
for x,y,sx,sy in [(21,-24,2.3,1.1),(9,-19,1.7,.7),(-10,-26,4,1.2),(19,9,2,1),(29,-11,3,.8)]:
    vs=[(x,y,height(x,y)+.025)]
    for k in range(48):
        t=k/48*math.tau;r=1+.1*math.sin(t*7)
        xx=x+math.cos(t)*sx*r;yy=y+math.sin(t)*sy*r;vs.append((xx,yy,height(x,y)+.025))
    mesh('Retreating water | shallow pool',vs,[(0,k+1,(k+1)%48+1) for k in range(48)],wet)
for i in range(35):
    y=-25+i*.5;x=15+math.sin(i*.17)*2
    for side in [-1,1]:
        o=stone('Footprint in new earth',(x+side*.23,y,height(x,y)+.002),(.09,.21,.003));o.rotation_euler[0]=0;o.rotation_euler[1]=0;o.data.materials.clear();o.data.materials.append(soil)
# Silt ridges follow the retreating water, deliberately quiet and irregular.
for j in range(7):
    y=-30-j*.67
    for a in range(-25,28,9):
        if random.random()<.3:continue
        pts=[(x*.5,y+.25*math.sin(x*.12+j*.5),height(x*.5,y)+.013) for x in range(a*2,(a+random.randint(3,7))*2)]
        line('Broken sediment ridge',pts,.018,soil,'03_Shore')
# Detailed mountain and first-growth modelling share the same authored scene helpers.
exec(compile(open(os.path.join(ROOT,'scripts','environment_detail.py'),encoding='utf-8').read(),'environment_detail.py','exec'),globals())
exec(compile(open(os.path.join(ROOT,'scripts','exile_boat.py'),encoding='utf-8').read(),'exile_boat.py','exec'),globals())
# Blender water and sky; browser supplies animated ocean and atmosphere.
water=material('Floodwater | pewter',(.13,.20,.23),.18)
box('Receding flood sea',(0,-115,-.815),(800,160,.05),water,'03_Shore',0)
world=bpy.data.worlds.new('After the rain');scene.world=world;world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.24,.32,.4,1);bg.inputs[1].default_value=.45
sky=world.node_tree.nodes.new('ShaderNodeTexSky')
sky_types=[i.identifier for i in sky.bl_rna.properties['sky_type'].enum_items]
sky.sky_type=next((i for i in sky_types if 'MULTIPLE' in i),sky_types[0])
sky.sun_elevation=.49;sky.sun_rotation=2.4;sky.altitude=.5;sky.air_density=1.4
if hasattr(sky,'aerosol_density'):sky.aerosol_density=2
world.node_tree.links.new(sky.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.24
fogmat=bpy.data.materials.new('Atmosphere | rain lifted mist');fogmat.use_nodes=True
nodes=fogmat.node_tree.nodes;nodes.clear();vol=nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=.0008;vol.inputs['Color'].default_value=(.65,.77,.85,1);vol.inputs['Anisotropy'].default_value=.24
output=nodes.new('ShaderNodeOutputMaterial');fogmat.node_tree.links.new(vol.outputs['Volume'],output.inputs['Volume'])
box('Atmosphere | native render volume',(0,35,65),(360,400,150),fogmat,'06_Lighting',0)
# A physical cloud deck with a broad clearing casts a soft, spatially grounded break in light.
cloudmat=bpy.data.materials.new('Atmosphere | torn storm deck');cloudmat.use_nodes=True
cn=cloudmat.node_tree.nodes;cl=cloudmat.node_tree.links;cn.clear()
geo=cn.new('ShaderNodeNewGeometry');tex=cn.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.018;tex.inputs['Detail'].default_value=4;tex.inputs['Roughness'].default_value=.7
cl.new(geo.outputs['Position'],tex.inputs['Vector'])
sub=cn.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=.44;sub.use_clamp=True;cl.new(tex.outputs['Fac'],sub.inputs[0])
strength=cn.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.06;cl.new(sub.outputs[0],strength.inputs[0])
offset=cn.new('ShaderNodeVectorMath');offset.operation='SUBTRACT';offset.inputs[1].default_value=(-33,164,95);cl.new(geo.outputs['Position'],offset.inputs[0])
flat=cn.new('ShaderNodeVectorMath');flat.operation='MULTIPLY';flat.inputs[1].default_value=(1,1,0);cl.new(offset.outputs[0],flat.inputs[0])
distance=cn.new('ShaderNodeVectorMath');distance.operation='LENGTH';cl.new(flat.outputs[0],distance.inputs[0])
opening=cn.new('ShaderNodeMapRange');opening.inputs['From Min'].default_value=34;opening.inputs['From Max'].default_value=78;cl.new(distance.outputs['Value'],opening.inputs['Value'])
density=cn.new('ShaderNodeMath');density.operation='MULTIPLY';cl.new(opening.outputs[0],density.inputs[0]);cl.new(strength.outputs[0],density.inputs[1])
cv=cn.new('ShaderNodeVolumePrincipled');cv.inputs['Color'].default_value=(.68,.75,.8,1);cv.inputs['Anisotropy'].default_value=.35;cl.new(density.outputs[0],cv.inputs['Density'])
out=cn.new('ShaderNodeOutputMaterial');cl.new(cv.outputs[0],out.inputs['Volume'])
box('Atmosphere | torn cloud canopy',(-10,180,95),(650,650,28),cloudmat,'06_Lighting',0)
def area(name,loc,power,col,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=col;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);groups['06_Lighting'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Cloudbreak | warm eastern light',(18,-26,34),5200,(1,.75,.48),18,(0,0,0))
area('Cold sky bounce',(-15,-8,20),3200,(.49,.67,1),24,(0,0,4))
area('Threshold reflected light',(8,-6,7),550,(1,.71,.42),5,(-2,-6,6))
sun=bpy.data.lights.new('Sun through retreating storm','SUN');sun.energy=2.1;sun.angle=.09;sun.color=(.86,.94,1)
o=bpy.data.objects.new('Sun through retreating storm',sun);groups['06_Lighting'].objects.link(o);o.rotation_euler=(-Vector((-20,100,58))).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Arrival | 35mm');co=bpy.data.objects.new('Arrival | 35mm',cam);groups['06_Lighting'].objects.link(co)
co.location=(24,-33,3.2);co.rotation_euler=(Vector((0,-1,6.4))-co.location).to_track_quat('-Z','Y').to_euler();cam.lens=28;scene.camera=co
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
if hasattr(scene.cycles,'volume_step_rate'):scene.cycles.volume_step_rate=2
if hasattr(scene.cycles,'volume_max_steps'):scene.cycles.volume_max_steps=256
scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene['Project']='ARARAT | The First Earth'
scene['Intent']='An explorable environment study. Original geometry with credited CC0 PBR materials. Not a shipping game.'
scene['Walk route']='Shore stone (17,-20) > gangway (15,-6) > threshold (5,-6) > olive table (-1.4,-6.2) > empty stalls.'
# Scanned wood fibres run in V, so align V with each board's long axis.
for obj in scene.objects:
    if obj.type=='MESH' and obj.data.materials and obj.data.materials[0] in woods and not obj.get('ark_uv_ready'):
        for layer in obj.data.uv_layers:
            for data in layer.data:
                u,v=data.uv;data.uv=(v,u)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
# Preserve authored geometry in .blend; export a resolved, batched runtime version.
for o in list(bpy.context.selected_objects):o.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','ARARAT_The_First_Earth.blend'))
print('BLEND_SAVED',len(scene.objects))
# Select meshes and curves only; cameras and lights are separately authored in runtime.
for o in scene.objects:
    o.select_set(o.type in {'MESH','CURVE'} and not o.name.startswith('Atmosphere'))
# Blender Bump nodes are not tangent-space normal textures. Disconnect only in the
# export process; the saved native project retains the authored bump shaders.
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED':
                for link in list(n.inputs['Normal'].links):
                    if link.from_node.type=='BUMP':m.node_tree.links.remove(link)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'ararat.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
print('GLB_EXPORTED')
