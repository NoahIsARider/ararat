"""One small, empty, double-ended shore boat: the possibility of leaving again."""
import bpy,math,os,json,random,bmesh
from mathutils import Vector,Matrix

def build_exile_boat():
    col=bpy.data.collections.get('09_Exile_Boat')
    if col:
        for obj in list(col.objects):bpy.data.objects.remove(obj,do_unlink=True)
    else:
        col=bpy.data.collections.new('09_Exile_Boat');bpy.context.scene.collection.children.link(col)
    rng=random.Random(734)
    root=bpy.data.objects.new('Exile | shore boat',None);col.objects.link(root)
    angle=.22;root.location=(26,-38.9,0);root.rotation_euler.z=angle
    water=-.79;length=4.7;depth=.88
    woods=[]
    for i in range(3):
        name='Boat | worn cedar %d'%i
        mat=bpy.data.materials.get(name)
        if not mat:
            mat=bpy.data.materials['Cedar | grain %02d'%i].copy();mat.name=name
        woods.append(mat)
    flax=bpy.data.materials.get('Flax | braided stair handline') or bpy.data.materials['Flax | weathered rope']
    linen=bpy.data.materials['Unbleached linen']
    def mesh(name,vs,fs,mat,uvs=None):
        data=bpy.data.meshes.new(name);data.from_pydata(vs,[],fs);data.update()
        bm=bmesh.new();bm.from_mesh(data)
        if bm.faces and all(e.is_manifold for e in bm.edges):bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data)
        bm.free()
        obj=bpy.data.objects.new('Exile | '+name,data);col.objects.link(obj);obj.parent=root;data.materials.append(mat)
        layer=data.uv_layers.new(name='UVMap')
        for loop in data.loops:
            v=data.vertices[loop.vertex_index].co
            layer.data[loop.index].uv=uvs[loop.vertex_index] if uvs else (v.x/.55,v.y/2.2)
        obj['exile_boat_part']=True;obj['ark_uv_ready']=True
        return obj
    def soften(obj,w=.008):
        mod=obj.modifiers.new('Worn boat timber edges','BEVEL');mod.width=w;mod.segments=2
        obj.modifiers.new('Weighted timber normals','WEIGHTED_NORMAL');return obj
    def box(name,pos,dims,mat=None,w=.008):
        x,y,z=[d/2 for d in dims]
        vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
        fs=[(2,6,4,0),(5,7,3,1),(4,5,1,0),(3,7,6,2),(1,3,2,0),(6,7,5,4)]
        obj=mesh(name,vs,fs,mat or rng.choice(woods));obj.location=pos
        axis=max(range(3),key=lambda a:dims[a]);other=0 if axis!=0 else 1
        for loop in obj.data.loops:
            v=obj.data.vertices[loop.vertex_index].co;obj.data.uv_layers.active.data[loop.index].uv=(v[other]/.6+rng.random()*.005,v[axis]/2.2)
        if w:soften(obj,min(w,min(dims)*.2))
        return obj
    def line(name,path,r,mat):
        data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
        sp=data.splines.new('POLY');sp.points.add(len(path)-1)
        for p,co in zip(sp.points,path):p.co=(*co,1)
        obj=bpy.data.objects.new('Exile | '+name,data);col.objects.link(obj);obj.parent=root;data.materials.append(mat);obj['exile_boat_part']=True
        return obj
    def beam(u):return .88*max(.025,1-u*u)**.55
    def bottom(u):return water-.28+.12*u*u
    def half(u,t):return beam(u)*(.22+.78*math.sin(t*math.pi/2)**.65)
    # Eight curved strakes meet closed ends and a continuous lower skin.
    for side in [-1,1]:
        for row in range(8):
            t0=row/8;t1=(row+1)/8-.003
            for part in range(4):
                ya=-length/2+part*length/4;yb=ya+length/4-.004;vv=[];uv=[]
                for t in [t0,t1]:
                    for k in range(13):
                        y=ya+(yb-ya)*k/12;u=y/(length/2)
                        vv.append((side*half(u,t),y,bottom(u)+depth*t));uv.append((t*1.4+row*.137,y/1.8+part*.11))
                ff=[(k,k+1,k+14,k+13) for k in range(12)]
                if side<0:ff=[tuple(reversed(f)) for f in ff]
                obj=mesh('curved cedar strake',vv,ff,woods[row%3],uv)
                mod=obj.modifiers.new('Real strake thickness','SOLIDIFY');mod.thickness=.045;mod.offset=-1;soften(obj,.005)
        vv=[]
        for j in range(41):
            y=-length/2+j*length/40;u=y/(length/2)
            for t in [0,.25,.5,.75,1]:vv.append((side*max(.01,half(u,t)-.025),y,bottom(u)+depth*t-.008))
        ff=[(j*5+k,(j+1)*5+k,(j+1)*5+k+1,j*5+k+1) for j in range(40) for k in range(4)]
        if side<0:ff=[tuple(reversed(f)) for f in ff]
        obj=mesh('continuous inner hull',vv,ff,woods[2]);mod=obj.modifiers.new('Inner hull thickness','SOLIDIFY');mod.thickness=.025;mod.offset=-1
        for r,zoff in [(.042,.005),(.026,-.09)]:
            path=[]
            for j in range(65):
                y=-length/2+j*length/64;u=y/(length/2);path.append((side*(half(u,1)-.006),y,bottom(u)+depth+zoff))
            line('bent gunwale',path,r,woods[1])
    # End transoms and keel leave no open view into the lower hull.
    for y in [-length/2,length/2]:
        u=y/(length/2);vv=[]
        for t in [0,.25,.5,.75,1]:vv.extend([(-half(u,t),y+math.copysign(.015,y),bottom(u)+depth*t),(half(u,t),y+math.copysign(.015,y),bottom(u)+depth*t)])
        ff=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(4)]
        if y>0:ff=[tuple(reversed(f)) for f in ff]
        obj=mesh('closed raised end',vv,ff,woods[0]);mod=obj.modifiers.new('End thickness','SOLIDIFY');mod.thickness=.055;mod.offset=-1
        line('end stem',[(0,y,bottom(u)-.02),(0,y,bottom(u)+depth+.05)],.045,woods[1])
    vv=[]
    for j in range(49):
        y=-length/2+j*length/48;u=y/(length/2);vv.extend([(-half(u,0),y,bottom(u)),(half(u,0),y,bottom(u))])
    obj=mesh('sealed bottom',vv,[(j*2,j*2+2,j*2+3,j*2+1) for j in range(48)],woods[2]);mod=obj.modifiers.new('Bottom thickness','SOLIDIFY');mod.thickness=.05
    line('curved keel',[(0,-length/2+j*length/40,bottom((-length/2+j*length/40)/(length/2))-.02) for j in range(41)],.045,woods[1])
    floor=water+.06;seat=water+.39
    # Clip each sole board to the hull at its actual elevation; no corners poke through.
    for x in [-.4,-.2,0,.2,.4]:
        vv=[]
        for j in range(23):
            y=-1.8+j*3.6/22;u=y/(length/2);t=max(0,min(1,(floor-bottom(u))/depth));limit=half(u,t)-.045
            vv.extend([(max(-limit,min(limit,x-.095)),y,floor),(max(-limit,min(limit,x+.095)),y,floor)])
        ff=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(22) if abs(vv[j*2][0]-vv[j*2+1][0])+abs(vv[j*2+2][0]-vv[j*2+3][0])>.002]
        if ff:
            obj=mesh('hull fitted dry sole plank',vv,ff,rng.choice(woods));mod=obj.modifiers.new('Sole board thickness','SOLIDIFY');mod.thickness=.05;soften(obj,.004)
    for y in [-1.82,-1.15,-.35,.5,1.2,1.85]:
        u=y/(length/2);path=[]
        for side,ts in [(-1,[1,.75,.5,.25,0]),(1,[0,.25,.5,.75,1])]:
            for t in ts:path.append((side*max(.01,half(u,t)-.063),y,bottom(u)+depth*t))
        line('hand bent inner rib',path,.024,woods[0])
    for y in [-1.15,.15,1.42]:
        u=y/(length/2);t=(seat-bottom(u))/depth;span=2*(half(u,t)-.055)
        box('rower thwart',(0,y,seat-.03),(span,.28,.06),woods[1])
        for x in [-span/2,span/2]:box('seated thwart cleat',(x,y,seat-.083),(.085,.38,.08),woods[2])
    # One oar lies on the thwarts; one small wrapped bundle occupies the shoreward seat.
    oar_z=seat+.027
    line('single ash oar shaft',[(-.28,1.95,oar_z),(-.24,1.5,oar_z),(.15,-1.3,oar_z)],.027,woods[0])
    vv=[(.09,-1.25,oar_z-.018),(.21,-1.25,oar_z-.018),(.35,-1.85,oar_z-.018),(.27,-2.,oar_z-.018),(.15,-1.94,oar_z-.018),(.06,-1.55,oar_z-.018)]
    obj=mesh('worn oar blade',vv,[tuple(range(6))],woods[0]);mod=obj.modifiers.new('Blade thickness','SOLIDIFY');mod.thickness=.028;soften(obj,.006)
    box('one linen bundle',(-.12,1.42,seat+.105),(.43,.36,.21),linen,.055)
    for side in [-1,1]:line('bundle tied seam',[(-.33,1.42+side*.075,seat+.07),(-.25,1.42+side*.075,seat+.21),(.09,1.42+side*.075,seat+.21),(.12,1.42+side*.075,seat+.07)],.007,flax)
    coil=[]
    for j in range(180):
        t=j/179*math.tau*3;r=.12+t*.003;coil.append((.22+math.cos(t)*r,.15+math.sin(t)*r,seat+.014))
    line('last loose mooring coil',coil,.012,flax)
    line('untied rope trailing in water',[(.25,.15,seat+.015),(.22,1.3,seat+.03),(.08,2.1,water+.65),(0,2.44,water+.74),(-.05,2.65,water+.2),(-.12,2.94,water-.035)],.012,flax)
    # A small carried cutting echoes the shore branch without adding another possession.
    olive=bpy.data.collections.get('05_Olive')
    transform=Matrix.Translation(Vector((-.20,-1.17,seat+.036)))@Matrix.Scale(.38,4)@Matrix.Translation(Vector((-16.4,20.1,-.569)))
    if olive:
        for source in list(olive.objects):
            coords=[source.matrix_world@Vector(c) for c in source.bound_box]
            if not coords or min(c.x for c in coords)<15 or max(c.y for c in coords)>-18:continue
            obj=source.copy();obj.data=source.data.copy();obj.name='Exile | carried olive cutting';col.objects.link(obj);obj.parent=root
            obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=transform@source.matrix_world;obj['exile_boat_part']=True
    # Keep native and realtime sea levels consistent.
    sea=bpy.data.objects.get('Receding flood sea')
    if sea:sea.location.z=water-.025
    project=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    navpath=os.path.join(project,'public','assets','navigation.json')
    with open(navpath) as f:nav=json.load(f)
    heading=[math.sin(angle),0,math.cos(angle)]
    nav['boat']={'position':[26,0,38.9],'heading':heading,'waterLevel':water,'floorLevel':floor,'seatLevel':seat,'stern':[26-math.sin(angle)*2.12,0,38.9-math.cos(angle)*2.12]}
    with open(navpath,'w') as f:json.dump(nav,f,indent=2)
    bpy.context.scene['Exile narrative']='A single boat faces the open sea. Reaching dry land is not the same as reaching home.'
    return nav['boat']

EXILE_BOAT=build_exile_boat()
