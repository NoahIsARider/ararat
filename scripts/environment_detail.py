"""Authored mountain relief and sparse post-flood ecology, executed by build_scene.py."""
def saturate(t):return max(0,min(1,t))
def lerp_color(a,b,t):return tuple(a[k]*(1-t)+b[k]*t for k in range(3))
def vertex_colours(obj,colours):
    layer=obj.data.color_attributes.new(name='Life_and_stone',type='FLOAT_COLOR',domain='CORNER')
    for loop in obj.data.loops:layer.data[loop.index].color=(*colours[loop.vertex_index],1)
def coloured_material(name):
    m=material(name,(1,1,1),.89)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    col=m.node_tree.nodes.new('ShaderNodeVertexColor');col.layer_name='Life_and_stone'
    m.node_tree.links.new(col.outputs['Color'],p.inputs['Base Color'])
    return m
mountain_mat=coloured_material('Mountain | flood washed stratified basalt')
nodes=mountain_mat.node_tree.nodes;links=mountain_mat.node_tree.links
p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=4
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.36;bump.inputs['Distance'].default_value=.16
links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])

# Distinct massif profiles share geology but have different tilted summits and catchments.
massifs=[(-72,67,57,29),(-31,88,56,35),(25,105,76,61),(82,99,61,41),(-88,146,71,48),(98,168,82,64)]
mountain_data=[]
def relief(x,y,cx,cy,rad,h,seed):
    warp=noise_vector(Vector((x*.026,y*.026,seed+1)))
    qx=(x-cx)/rad+warp.x*.11;qy=(y-cy)/rad+warp.y*.1
    best=-2
    # A fractured ridge has three staggered peaks, not a circular cone.
    for dx,dy,amp,rx,ry in [(-.37,.01,.69,.89,.93),(.10,.10,1.,1.02,.92),(.52,-.04,.63,.77,.86)]:
        xx=(qx-dx)/rx;yy=(qy-dy)/ry
        r=math.sqrt(xx*xx+yy*yy)
        if r>=1:continue
        ang=math.atan2(yy,xx)
        ravine=abs(math.sin(ang*7+math.sin(ang*3.1)*1.3+r*2.1+seed+warp.y*2))
        fluting=ravine**5*r*(1-r)*h*.18
        crag=noise_vector(Vector((x*.16,y*.16,seed))).x*.045*h*(1-r)
        micro=noise_vector(Vector((x*.48,y*.48,seed+12))).x*.016*h*(1-r)
        peak=(1-math.sqrt(r*r+.0036))**1.3*h*amp-fluting+crag+micro if r<.998 else -2
        best=max(best,peak)
    return best-1.1
for idx,(cx,cy,rad,h) in enumerate(massifs):
    n=181 if idx==2 else (129 if idx in [0,1,3] else 97)
    vertices=[];colours=[];uvs=[]
    for j in range(n):
        y=cy+(j/(n-1)-.5)*rad*3.1
        for i in range(n):
            x=cx+(i/(n-1)-.5)*rad*3.1;z=relief(x,y,cx,cy,rad,h,idx)
            dzx=(relief(x+.25,y,cx,cy,rad,h,idx)-relief(x-.25,y,cx,cy,rad,h,idx))*2
            dzy=(relief(x,y+.25,cx,cy,rad,h,idx)-relief(x,y-.25,cx,cy,rad,h,idx))*2
            slope=math.sqrt(dzx*dzx+dzy*dzy)
            strata=.5+.5*math.sin(z*1.9+math.sin(x*.12)*1.3)
            crag=noise_vector(Vector((x*.18,y*.18,idx))).x
            colour=lerp_color((.065,.082,.087),(.22,.25,.255),saturate(.3+strata*.4+crag*.4))
            # Washed scree has warmer grey undertones at its foot.
            colour=lerp_color(colour,(.14,.145,.12),saturate(1-z/(h*.25))*.45)
            snow=saturate((z/h-.62)*6)*saturate(1.3-slope*.7)
            # Small snow pockets remain in erosion gullies rather than a clean white cap.
            snow*=saturate(.6+noise_vector(Vector((x*.09,y*.09,17))).x)
            colour=lerp_color(colour,(.62,.73,.77),snow)
            vertices.append((x,y,z));colours.append(colour);uvs.append((x*.05,y*.05))
    faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(n-1) for i in range(n-1)]
    obj=mesh('Ararat | fractured massif %02d'%idx,vertices,faces,mountain_mat,'04_Mountains',uvs)
    vertex_colours(obj,colours)
    for poly in obj.data.polygons:poly.use_smooth=True
    mountain_data.append((cx,cy,rad,h,idx))

# Shore talus sits in exposed mud at the toe of the mountains. A low setting
# lets the actual mountain surface swallow stones where the slope advances.
bpy.context.view_layer.update()
for i in range(48):
    x=random.uniform(-55,69);y=random.uniform(32,48)
    z=height(x,y)
    s=random.uniform(.5,2.2)
    obj=stone('Mountain foot | fractured talus',(x,y,z-s*.16),(s,s*.8,s*random.uniform(.4,.9)),'04_Mountains')

# Botanical detail is clustered around silt pockets and shelter, with large bare areas.
grass_mat=coloured_material('Vegetation | washed sedge blades')
fern_mat=coloured_material('Vegetation | first fern fronds')
moss_mat=coloured_material('Vegetation | wet rock moss')
seed_mat=material('Vegetation | weathered seed husks',(.16,.14,.085),.96)
sprout_mat=material('Vegetation | first shoots',(.055,.15,.075),.66)

def ribbon_blade(vs,fs,cs,base,angle,length,width,bend,colour):
    start=len(vs);x,y,z=base
    side=Vector((-math.sin(angle),math.cos(angle),0))
    lean=Vector((math.cos(angle),math.sin(angle),0))
    for j in range(7):
        t=j/6;centre=Vector(base)+lean*(bend*t*t)+Vector((0,0,length*(t-.25*t*t)))
        w=width*(math.sin(t*math.pi)**.7+.04)*(1-t*.6)
        for k in [-1,0,1]:
            pos=centre+side*w*k+Vector((0,0,(1-abs(k))*.0015*math.sin(t*math.pi)))
            vs.append(tuple(pos));cs.append(lerp_color((.10,.085,.046),colour,saturate(t*3)))
    for j in range(6):
        for k in range(2):a=start+j*3+k;fs.append((a,a+1,a+4,a+3))

patches=[(25,-26,2.2),(28,-17,2.6),(28,-3,3.4),(24,12,3.5),(18,25,3),(-14,-21,2.8),(-19,-8,4),(-17,16,3),(13,-27,1.4),(32,25,4)]
for idx,(px,py,spread) in enumerate(patches):
    vs=[];fs=[];cs=[]
    for clump in range(random.randint(14,25)):
        x=random.gauss(px,spread*.55);y=random.gauss(py,spread*.4)
        if 4<x<16 and -8.4<y<-3.7:continue
        clump_angle=random.uniform(.6,1.5)
        for blade in range(random.randint(13,23)):
            xx=x+random.uniform(-.11,.11);yy=y+random.uniform(-.11,.11)
            length=random.uniform(.13,.48);angle=clump_angle+random.uniform(-.65,.65)
            colour=random.choice([(.045,.075,.044),(.07,.105,.065),(.12,.13,.075),(.09,.12,.09)])
            ribbon_blade(vs,fs,cs,(xx,yy,height(xx,yy)+.012),angle,length,random.uniform(.009,.019),random.uniform(.08,.27),colour)
    if vs:
        o=mesh('First growth | sedge island %02d'%idx,vs,fs,grass_mat,'08_First_Growth');vertex_colours(o,cs)
        for poly in o.data.polygons:poly.use_smooth=True

def leaflet(vs,fs,cs,a,b,width,col):
    a=Vector(a);b=Vector(b);axis=b-a;side=Vector((-axis.y,axis.x,0)).normalized()*width;start=len(vs)
    for j in range(6):
        t=j/5;c=a+axis*t+Vector((0,0,math.sin(t*math.pi)*width*.2));w=math.sin(t*math.pi)
        vs.extend([tuple(c-side*w),tuple(c+Vector((0,0,width*.13*w))),tuple(c+side*w)])
        cs.extend([col,lerp_color(col,(.22,.28,.12),.28),col])
    for j in range(5):
        for k in range(2):a=start+j*3+k;fs.append((a,a+1,a+4,a+3))

for idx,(x,y) in enumerate([(25,-17),(28,-3),(-14,-20),(-18,15),(24,14),(31,25),(13,-28)]):
    z=height(x,y);vs=[];fs=[];cs=[]
    for frond in range(random.randint(5,8)):
        angle=random.random()*math.tau;length=random.uniform(.35,.64);out=Vector((math.cos(angle),math.sin(angle),0))
        side=Vector((-out.y,out.x,0));base=Vector((x,y,z+.025))
        path=[base+out*(length*t*.85)+Vector((0,0,length*(1.65*t-1.25*t*t))) for t in [j/16 for j in range(17)]]
        line('First fern | curved rachis',[tuple(p) for p in path],.0028,sprout_mat,'08_First_Growth')
        for j in range(2,15):
            t=j/16;centre=path[j];extent=length*.24*math.sin(t*math.pi)**.7
            for s in [-1,1]:
                tip=centre+side*(s*extent)+out*extent*.32+Vector((0,0,.009))
                leaflet(vs,fs,cs,centre,tip,extent*.19,random.choice([(.025,.08,.036),(.045,.12,.05),(.075,.14,.065)]))
    o=mesh('First growth | fern %02d'%idx,vs,fs,fern_mat,'08_First_Growth');vertex_colours(o,cs)
    for poly in o.data.polygons:poly.use_smooth=True

# Tiny opposing cotyledons are the first new life, deliberately not a lush garden.
for idx in range(38):
    px,py,spread=random.choice(patches);x=random.gauss(px,spread*.5);y=random.gauss(py,spread*.4)
    z=height(x,y);angle=random.random()*math.tau;vs=[];fs=[];cs=[]
    stem=Vector((x,y,z+random.uniform(.045,.10)))
    line('First shoot | tender stem',[(x,y,z),tuple(stem)],.002,sprout_mat,'08_First_Growth')
    for side in [-1,1]:
        end=stem+Vector((math.cos(angle)*.065*side,math.sin(angle)*.065*side,.016))
        leaflet(vs,fs,cs,stem,end,.018,(.07,.18,.085))
    o=mesh('First growth | seedling',vs,fs,fern_mat,'08_First_Growth');vertex_colours(o,cs)

# A sheltered stone forms a readable near-view vignette with the first fern.
nursery=stone('Sheltered moss nursery stone',(24.35,-17.2,height(24.35,-17.2)+.12),(.65,.52,.3))
nursery.rotation_euler=(0,0,.2)
# Moss hugs actual ray-cast rock surfaces rather than floating green discs.
bpy.context.view_layer.update()
rock_objects=[o for o in groups['03_Shore'].objects if o.name.startswith('Water worn shore stone') and max(o.dimensions)>.55]
for idx,obj in enumerate([nursery]+random.sample(rock_objects,min(31,len(rock_objects)))):
    inv=obj.matrix_world.inverted();centre=obj.location;vs=[];fs=[];cs=[]
    radius=min(obj.dimensions.x,obj.dimensions.y)*random.uniform(.14,.26)
    grid=15
    for j in range(grid):
        for i in range(grid):
            xx=centre.x+(i/(grid-1)-.5)*radius*2;yy=centre.y+(j/(grid-1)-.5)*radius*2
            origin=inv@Vector((xx,yy,centre.z+4));direction=(inv.to_3x3()@Vector((0,0,-1))).normalized()
            hit,co,normal,face=obj.ray_cast(origin,direction)
            pos=obj.matrix_world@co if hit else Vector((xx,yy,centre.z))
            pos.z+=.006;vs.append(tuple(pos));cs.append(random.choice([(.012,.027,.012),(.028,.052,.019),(.052,.075,.029)]))
    for j in range(grid-1):
        for i in range(grid-1):
            if ((i-6.5)/7)**2+((j-6.5)/7)**2>random.uniform(.6,1.05):continue
            if noise_vector(Vector((i*.72,j*.72,idx+10))).x<-.06:continue
            a=j*grid+i;fs.append((a,a+1,a+grid+1,a+grid))
    o=mesh('First growth | rock moss %02d'%idx,vs,fs,moss_mat,'08_First_Growth');vertex_colours(o,cs)
    for poly in o.data.polygons:poly.use_smooth=True

print('MOUNTAINS_AND_FIRST_GROWTH_MODELLED',flush=True)
