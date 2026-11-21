"""Build the ark, hatch and timber stair from shared, inspectable dimensions.

Executed both by the full scene generator and by rebuild_ark.py. Surrounding
landscape and surviving interior props are preserved by the incremental path.
"""
import bpy, bmesh, math, random, os, json
from mathutils import Vector

def rebuild_ark_structure():
    rng=random.Random(10297)
    ark=bpy.data.collections.get('01_Ark')
    inside=bpy.data.collections.get('02_Interior')
    for obj in list(ark.objects):bpy.data.objects.remove(obj,do_unlink=True)
    replaced=('Interior floorboard','Interior frame upright','Interior cross tie','Knee brace','Empty stall slat','Ark |')
    for obj in list(inside.objects):
        if obj.name.startswith(replaced):bpy.data.objects.remove(obj,do_unlink=True)
    woods=[bpy.data.materials.get('Cedar | grain %02d'%i) for i in range(5)]
    def plain(name,colour,rough=.88):
        mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes=True;p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Base Color'].default_value=(*colour,1);p.inputs['Roughness'].default_value=rough
        return mat
    caulk=plain('Pitch | sealed structural skin',(.022,.025,.022))
    endgrain=plain('Cedar | cut end grain',(.16,.105,.06))
    flax=plain('Flax | braided stair handline',(.13,.105,.064),.96)
    # Low-contrast growth rings are used on actual cut faces and pegs, never side grain.
    end_image=bpy.data.images.get('Cedar | annual rings')
    if end_image is None:
        size=256;end_image=bpy.data.images.new('Cedar | annual rings',width=size,height=size)
        px=[]
        for j in range(size):
            for i in range(size):
                x=(i/size-.48)*2;y=(j/size-.51)*2;r=math.sqrt(x*x+y*y)
                grain=(.5+.5*math.sin((r+.025*math.sin(x*13+y*8))*93))**8
                c=.21-grain*.045+.012*math.sin(x*41+y*29)
                px.extend((c,c*.76,c*.50,1))
        end_image.pixels.foreach_set(px);end_image.pack()
    p=next(n for n in endgrain.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    tx=endgrain.node_tree.nodes.new('ShaderNodeTexImage');tx.image=end_image
    endgrain.node_tree.links.new(tx.outputs[0],p.inputs['Base Color'])
    def raw(name,verts,faces,mat=caulk,collection=ark,uvs=None):
        data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
        bm=bmesh.new();bm.from_mesh(data)
        if bm.faces and all(edge.is_manifold for edge in bm.edges):
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);data.update()
        bm.free()
        obj=bpy.data.objects.new(name,data);collection.objects.link(obj);data.materials.append(mat)
        uv=data.uv_layers.new(name='UVMap')
        for loop in data.loops:
            co=verts[loop.vertex_index]
            uv.data[loop.index].uv=uvs[loop.vertex_index] if uvs else (co[0]*.5,co[1]*.5)
        obj['ark_uv_ready']=True
        return obj
    def bevel(obj,width=.018):
        mod=obj.modifiers.new('Hand softened timber edges','BEVEL');mod.width=width;mod.segments=3
        obj.modifiers.new('Face weighted corner normals','WEIGHTED_NORMAL')
        return obj
    def timber(name,location,dimensions,mat=None,collection=ark,edge=.018):
        dims=tuple(dimensions);sx,sy,sz=[d/2 for d in dims]
        verts=[(-sx,-sy,-sz),(-sx,-sy,sz),(-sx,sy,-sz),(-sx,sy,sz),(sx,-sy,-sz),(sx,-sy,sz),(sx,sy,-sz),(sx,sy,sz)]
        faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
        obj=raw(name,verts,faces,mat or rng.choice(woods),collection);obj.location=location
        obj.data.materials.append(endgrain)
        axis=max(range(3),key=lambda a:dims[a]);offset=rng.random()*2
        for poly in obj.data.polygons:
            cut=abs(poly.normal[axis])>.9
            other=[i for i in range(3) if i!=axis]
            if not cut:
                cross=max(other,key=lambda a:abs(dims[a]) if abs(poly.normal[a])<.9 else -1)
            else:poly.material_index=1
            for li in poly.loop_indices:
                co=obj.data.vertices[obj.data.loops[li].vertex_index].co
                obj.data.uv_layers.active.data[li].uv=((co[other[0]]/max(dims[other[0]],.01)+.5,co[other[1]]/max(dims[other[1]],.01)+.5) if cut else (co[cross]/.58+offset,co[axis]/2.4+offset))
        if edge:bevel(obj,min(edge,min(dims)*.20))
        return obj
    def strut(name,a,b,size=.16,collection=ark):
        a=Vector(a);b=Vector(b)
        obj=timber(name,(a+b)/2,(size,size,(b-a).length),collection=collection)
        obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return obj
    def tube(name,points,radius,mat=flax,collection=ark):
        cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=2
        sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
        for p,co in zip(sp.points,points):p.co=(*co,1)
        obj=bpy.data.objects.new(name,cu);collection.objects.link(obj);cu.materials.append(mat);return obj
    def peg(name,location,axis='X',radius=.036,length=.06):
        verts=[]
        for t in [-length/2,length/2]:
            for k in range(12):
                angle=k/12*math.tau;v=[radius*math.cos(angle),radius*math.sin(angle),t]
                if axis=='X':v=[t,v[0],v[1]]
                elif axis=='Y':v=[v[0],t,v[1]]
                verts.append(tuple(Vector(v)+Vector(location)))
        faces=[(k,(k+1)%12,(k+1)%12+12,k+12) for k in range(12)]+[tuple(reversed(range(12))),tuple(range(12,24))]
        return bevel(raw(name,verts,faces,endgrain),.003)
    def ground(x,y):
        return .14*math.sin(x*.23)*math.cos(y*.15)+.09*math.cos(y*.4)+.005*(y+15)-max(0,-y-26)*.07-max(0,-x-22)*.045
    def halfwidth(y,z):
        upper=1.5+4.2*math.sqrt(max(0,min(1,(z-1)/9)))
        if z<1:upper=.28+(1.5-.28)*max(0,(z-.12)/.88)**.65
        return upper*math.sqrt(max(.04,1-(abs(y)/22.1)**4))
    def skin_width(y,z):return max(.02,halfwidth(y,z)-.10)
    deck=4.97;door_y=(-7.4,-4.6);door_z=(deck,8.15);end=21.9
    def outside_door(ya,yb,za,zb,side):
        if side<0 or yb<=door_y[0] or ya>=door_y[1] or zb<=door_z[0] or za>=door_z[1]:return [(ya,yb,za,zb)]
        out=[]
        if za<door_z[0]:out.append((ya,yb,za,door_z[0]))
        if zb>door_z[1]:out.append((ya,yb,door_z[1],zb))
        lo=max(za,door_z[0]);hi=min(zb,door_z[1])
        if ya<door_y[0]:out.append((ya,door_y[0],lo,hi))
        if yb>door_y[1]:out.append((door_y[1],yb,lo,hi))
        return [r for r in out if r[1]-r[0]>.002 and r[3]-r[2]>.002]

    # One welded, solidified skin closes the bottom and both ends under all board seams.
    ys=sorted(set([-end,end,*door_y]+[-end+i*(end*2/58) for i in range(59)]))
    zs=sorted(set([.12,.45,.72,1.,9.97,*door_z]+[1+i*.64 for i in range(15) if 1+i*.64<9.97]))
    verts=[];faces=[];indices={}
    def vert(co):
        key=tuple(round(c,6) for c in co)
        if key not in indices:indices[key]=len(verts);verts.append(co)
        return indices[key]
    def face(coords):faces.append(tuple(vert(c) for c in coords))
    for side in [-1,1]:
        for j in range(len(ys)-1):
            for k in range(len(zs)-1):
                ya,yb=ys[j:j+2];za,zb=zs[k:k+2]
                if side>0 and door_y[0]<=ya and yb<=door_y[1] and door_z[0]<=za and zb<=door_z[1]:continue
                coords=[(side*skin_width(y,z),y,z) for y,z in [(ya,za),(yb,za),(yb,zb),(ya,zb)]]
                face(coords if side>0 else list(reversed(coords)))
    for ya,yb in zip(ys[:-1],ys[1:]):
        face([(-skin_width(ya,.12),ya,.12),(-skin_width(yb,.12),yb,.12),(skin_width(yb,.12),yb,.12),(skin_width(ya,.12),ya,.12)])
    for y in [-end,end]:
        for za,zb in zip(zs[:-1],zs[1:]):
            coords=[(-skin_width(y,za),y,za),(skin_width(y,za),y,za),(skin_width(y,zb),y,zb),(-skin_width(y,zb),y,zb)]
            face(coords if y<0 else list(reversed(coords)))
    skin=raw('Ark | sealed bilge and transom skin',verts,faces,caulk)
    solid=skin.modifiers.new('Continuous inner wall thickness','SOLIDIFY');solid.thickness=.14;solid.offset=-1
    skin['structural_check']='Welded sides, bilge and transoms; deliberate open deck and clean hatch aperture.'

    # Individually solid boards have staggered joints and exactly cropped hatch edges.
    rows=[(.14,.46),(.46,.74),(.74,1.01)]+[(1+i*.64,1+i*.64+.622) for i in range(14)]
    def side_board(name,ya,yb,za,zb,side,inset=0,mat=None):
        vv=[];uv=[];off=rng.random()*3
        for z in [za,zb]:
            for k in range(7):
                y=ya+(yb-ya)*k/6;vv.append((side*(halfwidth(y,z)-inset),y,z));uv.append(((z-za)/.6+off,(y-ya)/2.7+off))
        ff=[(k,k+1,k+8,k+7) for k in range(6)]
        if side<0:ff=[tuple(reversed(f)) for f in ff]
        obj=raw(name,vv,ff,mat or rng.choice(woods),uvs=uv)
        sol=obj.modifiers.new('Solid cedar board','SOLIDIFY');sol.thickness=.13;sol.offset=-1
        bevel(obj,.009);return obj
    for side in [-1,1]:
        for row,(za,zb) in enumerate(rows):
            ya=-end
            while ya<end-.01:
                yb=min(end,ya+(1.6 if ya==-end and row%2 else 3.12))
                for rect in outside_door(ya,yb,za,zb,side):side_board('Ark | fitted outer cedar course %02d'%row,*rect,side)
                ya=yb+.015
        # The lining sits inside the sealed skin and follows the same aperture.
        for row in range(9):
            za=4.8+row*.58;zb=min(9.97,za+.573)
            for j in range(15):
                ya=-end+j*end*2/15;yb=min(end,ya+end*2/15-.008)
                for rect in outside_door(ya,yb,za,zb,side):side_board('Ark | interior cedar lining',*rect,side,.29)
    for y in [-end,end]:
        board_y=y+math.copysign(.035,y)
        for row,(za,zb) in enumerate(rows):
            vv=[(-halfwidth(y,za),board_y,za),(halfwidth(y,za),board_y,za),(halfwidth(y,zb),board_y,zb),(-halfwidth(y,zb),board_y,zb)]
            ff=[(0,1,2,3) if y<0 else (3,2,1,0)]
            obj=raw('Ark | fitted end transom course',vv,ff,rng.choice(woods),uvs=[(0,0),(0,1.5),(1,1.5),(1,0)])
            so=obj.modifiers.new('Transom cedar thickness','SOLIDIFY');so.thickness=.16;so.offset=-1;bevel(obj,.009)
        timber('Ark | scarfed stem post',(0,y,.12+10.05/2),(.36,.42,10.05))
    timber('Ark | grounded continuous keel',(0,0,.24),(.36,43.8,.46))
    # Wale sections and curved ribs physically overlap the shell, including the narrow ends.
    for side in [-1,1]:
        for z in [2.0,4.48,8.60,9.97]:
            vv=[]
            for y in ys:
                x=side*(halfwidth(y,z)+.065)
                vv.extend([(x-side*.11,y,z-.12),(x+side*.11,y,z-.12),(x+side*.11,y,z+.12),(x-side*.11,y,z+.12)])
            ff=[]
            for i in range(len(ys)-1):
                for k in range(4):a=i*4+k;b=i*4+(k+1)%4;ff.append((a,b,b+4,a+4))
            ff+=[(3,2,1,0),tuple(range((len(ys)-1)*4,len(ys)*4))]
            obj=raw('Ark | fitted longitudinal wale',vv,ff,rng.choice(woods),uvs=[((k%4)*.25,ys[k//4]/2.6) for k in range(len(vv))]);bevel(obj,.018)
            for y in range(-20,21,4):peg('Ark | wale fastening',(side*(halfwidth(y,z)+.187),y,z))
        for y in range(-20,21,4):
            path=[(side*(halfwidth(y,z)+.035),y,z) for z in [.4+i*9.55/44 for i in range(45)]]
            tube('Ark | bent outer rib',path,.095,rng.choice(woods))

    # The deck follows the hull plan rather than extending as a rectangle through its sides.
    def deck_limit(y):return halfwidth(y,deck)-.31
    for row in range(16):
        ya=-20.8+row*2.6;yb=ya+2.59
        for col in range(-9,10):
            x0=col*.46-.222;x1=col*.46+.222;vv=[];uv=[]
            samples=9
            for k in range(samples):
                y=ya+(yb-ya)*k/(samples-1);lim=deck_limit(y)
                for x in [max(-lim,min(lim,x0)),max(-lim,min(lim,x1))]:vv.append((x,y,deck));uv.append((x/.55,y/2.5))
            ff=[]
            for k in range(samples-1):
                a=k*2
                if abs(vv[a+1][0]-vv[a][0])+abs(vv[a+3][0]-vv[a+2][0])>.004:ff.append((a,a+1,a+3,a+2))
            if not ff:continue
            obj=raw('Ark | hull fitted deck plank',vv,ff,rng.choice(woods),inside,uv)
            bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(obj.data);bm.free()
            so=obj.modifiers.new('Deck thickness','SOLIDIFY');so.thickness=.18;so.offset=-1;bevel(obj,.006)
    vv=[]
    for i in range(85):
        y=-20.8+i*41.6/84;lim=deck_limit(y);vv.extend([(-lim,y,deck-.14),(lim,y,deck-.14)])
    obj=raw('Ark | continuous deck caulking',vv,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(84)],caulk,inside)
    so=obj.modifiers.new('Subdeck backing','SOLIDIFY');so.thickness=.06
    for y in [-18,-14,-10,-2,6,14,18]:
        x=deck_limit(y)-.22;head=9.53;outer=halfwidth(y,9.7)-.2
        for side in [-1,1]:
            timber('Ark | deck seated frame upright',(side*x,y,(deck+head)/2),(.26,.30,head-deck),collection=inside)
            strut('Ark | mortised knee brace',(side*x,y,8.25),(side*(x-1.0),y,head),.21,inside)
        timber('Ark | housed cross tie',(0,y,9.68),(outer*2,.32,.3),collection=inside)
    for y in [3,9,15]:
        outer=deck_limit(y)-.12
        for side in [-1,1]:
            for x in [1.45,outer]:timber('Ark | stall pegged upright',(side*x,y,5.67),(.13,.15,1.4),collection=inside)
            for k in range(4):timber('Ark | stall worn rail',(side*(1.45+outer)/2,y,5.32+k*.34),(outer-1.45,.11,.10),collection=inside)

    # Roof plan, eave supports and gables all derive from the hull's crown width.
    eave=10.78;ridge=12.96
    def roof_width(y):return halfwidth(max(-end,min(end,y)),9.97)+.19
    roof_frames=[-end]+[-22.05+i*44.1/16 for i in range(1,16)]+[end]
    for y in roof_frames:
        ex=roof_width(y)-.12
        for side in [-1,1]:
            timber('Ark | seated clerestory post',(side*(ex-.13),y,(10.02+eave)/2),(.14,.16,eave-10.02))
            strut('Ark | roof rafter',(side*ex,y,eave-.22),(0,y,ridge-.22),.20)
        collar_span=2*ex*(ridge-.22-11.75)/(ridge-eave)+.12
        timber('Ark | roof collar tie',(0,y,11.75),(collar_span,.16,.16))
    for side in [-1,1]:
        # Recessed underlay closes board joints without coplanar overlapping faces.
        vv=[]
        roof_ys=[-22.05,*ys,22.05]
        for y in roof_ys:
            vv.extend([(0,y,ridge-.31),(side*roof_width(y),y,eave-.31)])
        ff=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(roof_ys)-1)]
        if side<0:ff=[tuple(reversed(f)) for f in ff]
        backing=raw('Ark | recessed roof underlay',vv,ff,caulk)
        so=backing.modifiers.new('Roof underlay thickness','SOLIDIFY');so.thickness=.08;so.offset=-1
        for row in range(16):
            ya=-22.05+row*44.10/16;yb=ya+44.1/16
            for col in range(15):
                t0=col/15;t1=(col+1)/15;vv=[];uv=[]
                for y in [ya,(ya+yb)/2,yb]:
                    for t in [t0,t1]:
                        vv.append((side*roof_width(y)*t,y,ridge-(ridge-eave)*t));uv.append((t*roof_width(y)/.56,y/2.6))
                ff=[(0,1,3,2),(2,3,5,4)]
                if side<0:ff=[tuple(reversed(face)) for face in ff]
                obj=raw('Ark | fitted roof weatherboard',vv,ff,rng.choice(woods),uvs=uv)
                so=obj.modifiers.new('Overlapping roof board','SOLIDIFY');so.thickness=.14;bevel(obj,.008)
        # Raised wooden cover strips seal long board joints; no dark perforated roof grid.
        batten_ys=[-22.05+j*44.1/32 for j in range(33)]
        for joint in range(1,15):
            t=joint/15;vv=[];uv=[]
            for y in batten_ys:
                centre=side*roof_width(y)*t;z=ridge-(ridge-eave)*t
                vv.extend([(centre-.028,y,z-.018),(centre+.028,y,z-.018),(centre+.028,y,z+.027),(centre-.028,y,z+.027)])
                uv.extend([(0,y/2.6),(.15,y/2.6),(.3,y/2.6),(.45,y/2.6)])
            ff=[]
            for j in range(len(batten_ys)-1):
                for k in range(4):a=j*4+k;b=j*4+(k+1)%4;ff.append((a,b,b+4,a+4))
            ff.extend([(3,2,1,0),tuple(range((len(batten_ys)-1)*4,len(batten_ys)*4))])
            obj=raw('Ark | roof seam batten',vv,ff,woods[joint%5],uvs=uv);bevel(obj,.005)
        tube('Ark | continuous eave bearer',[(side*(roof_width(y)-.1),y,eave-.24) for y in ys],.15,woods[2])
    timber('Ark | ridge weather cap',(0,0,ridge+.065),(.32,44.5,.18))
    for y in [-end,end]:
        ex=roof_width(y)
        cap_y=y+math.copysign(.035,y)
        obj=raw('Ark | closed end gable',[(-ex,cap_y,9.96),(ex,cap_y,9.96),(ex,cap_y,eave),(0,cap_y,ridge),(-ex,cap_y,eave)],[(0,1,2,3,4) if y<0 else (4,3,2,1,0)],woods[2],uvs=[(0,0),(1,0),(1,1),(.5,1.8),(0,1)])
        so=obj.modifiers.new('Gable boarding','SOLIDIFY');so.thickness=.18
        for side in [-1,1]:strut('Ark | gable bargeboard',(side*ex,y,eave),(0,y,ridge+.02),.18)

    # A built-out hatch coaming closes the gap between curved hull and vertical door frame.
    front=5.55;landing_min=3.45;landing_max=6.6;half=1.31
    for side_y in door_y:
        for row in range(6):
            za=deck+row*(door_z[1]-deck)/6;zb=deck+(row+1)*(door_z[1]-deck)/6
            vv=[(halfwidth(side_y,za)-.10,side_y,za),(front+.13,side_y,za),(front+.13,side_y,zb),(halfwidth(side_y,zb)-.10,side_y,zb)]
            obj=raw('Hatch | fitted coaming cheek',vv,[(0,1,2,3)],woods[row%5],uvs=[(0,0),(0,1),(1,1),(1,0)])
            so=obj.modifiers.new('Coaming cheek thickness','SOLIDIFY');so.thickness=.16
        timber('Hatch | housed jamb',(front,side_y,(deck+8.28)/2),(.32,.28,8.28-deck))
        for z in [5.23,7.9]:peg('Hatch | wooden frame pin',(front+.18,side_y,z),radius=.044)
    timber('Hatch | lintel with seated ends',(front,-6,8.27),(.40,3.28,.34))
    timber('Hatch | continuous threshold sill',(front,-6,deck-.105),(.44,2.9,.21))
    timber('Hatch | rain hood',((halfwidth(-6,8.2)+6.03)/2,-6,8.52),(1.16,3.45,.15))
    for y in [-7.18,-4.82]:strut('Hatch | hood knee',(front,y,7.80),(6.02,y,8.43),.13)
    def platform(name,xmin,xmax,z):
        n=max(2,math.ceil((xmax-xmin)/.27));span=(xmax-xmin)/n
        for i in range(n):timber(name+' plank',(xmin+(i+.5)*span,-6,z-.075),(span-.008,half*2,.15),edge=.009)
        for y in [-7.1,-4.9]:timber(name+' bearer',((xmin+xmax)/2,y,z-.245),(xmax-xmin,.22,.25))
    platform('Landing | connected hatch platform',landing_min,landing_max,deck)

    # Horizontal treads and closed risers, with one shared stair surface for runtime walking.
    run=10.;bottom_x=landing_max+run;count=28;going=run/count
    bottom_z=max(ground(x,y) for x in [bottom_x,bottom_x+1.4] for y in [-7.31,-4.69])+.14
    rise=(deck-bottom_z)/count
    platform('Landing | grounded foot platform',bottom_x,bottom_x+1.4,bottom_z)
    for i in range(count):
        outer=bottom_x-i*going;inner=outer-going;z=bottom_z+(i+1)*rise
        obj=timber('Stair | horizontal tread %02d'%(i+1),((inner+outer)/2,-6,z-.056),(going+.022,2.42,.112),edge=.009)
        obj['tread_index']=i+1;obj['top_elevation']=z
        timber('Stair | closed riser %02d'%(i+1),(outer-.012,-6,z-rise*.5-.03),(.065,2.30,rise+.06),edge=.006)
        for y in [-7.02,-4.98]:peg('Stair | tread fixing',(outer-going*.5,y,z+.006),'Z',.025,.025)
    for y in [-7.15,-4.85]:
        profile=[]
        for i in range(count):
            outer=bottom_x-i*going;inner=outer-going;z=bottom_z+(i+1)*rise-.065
            profile.extend([(outer,z),(inner,z)])
        profile.extend([(landing_max,deck-.62),(bottom_x,bottom_z-.62)])
        n=len(profile);vv=[(x,yy,z) for yy in [y-.10,y+.10] for x,z in profile]
        ff=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        uv=[((z-(bottom_z+(bottom_x-x)/run*(deck-bottom_z)))/.6,(bottom_x-x)/2.6) for yy in [0,1] for x,z in profile]
        obj=raw('Stair | continuous housed side stringer',vv,ff,woods[3],uvs=uv);bevel(obj,.009)
    def surface(x):
        if x>=bottom_x:return bottom_z
        if x<=landing_max:return deck
        return bottom_z+min(count,max(1,math.floor((bottom_x-x)/going)+1))*rise
    # Bearing frames and diagonals terminate in terrain-seated pads.
    for x in [bottom_x+.7,14.25,11.0,7.7,5.95]:
        seat=surface(x)-(.22 if x>bottom_x else .49)
        for y in [-7.03,-4.97]:
            soil_z=ground(x,y);padtop=soil_z+.16
            pad=timber('Stair | mud seated bearing pad',(x,y,soil_z+.065),(.58,.54,.19),edge=.018)
            pad['ground_elevation']=soil_z
            if seat>padtop+.05:
                timber('Stair | bearing upright',(x,y,(padtop+seat)/2),(.20,.22,seat-padtop))
        timber('Stair | transverse bearing cap',(x,-6,seat+.06),(.30,2.72,.18))
        if seat>1.0:
            for sign in [-1,1]:strut('Stair | transverse diagonal brace',(x,-6+sign*.95,ground(x,-6+sign*.95)+.25),(x,-6-sign*.98,seat-.06),.12)
    # Posts are attached to stringers/platforms; ropes end in actual wraps around those posts.
    post_x=[bottom_x+.8,14.35,11.8,9.2,6.4,front]
    for y in [-7.18,-4.82]:
        tops=[]
        for x in post_x:
            z=surface(x)
            if x!=front:
                timber('Stair | pegged guard post',(x,y,z+.48),(.14,.16,1.18))
                timber('Stair | post socket',(x,y,z-.05),(.26,.27,.22),edge=.012)
                peg('Stair | post through peg',(x,y+.10,z+.11),'Y',.032,.10)
            anchor_y=door_y[0] if y<-6 else door_y[1]
            anchor_y=anchor_y if x==front else y
            top=(x,anchor_y,z+1.01);tops.append(top)
            wrap=[]
            for j in range(55):
                angle=j/54*math.tau*2.2
                dx=math.cos(angle);dy=math.sin(angle)
                if x==front:dx=math.copysign(abs(dx)**.3*.173,dx);dy=math.copysign(abs(dy)**.3*.153,dy)
                else:dx*=.105;dy*=.105
                wrap.append((x+dx,anchor_y+dy,top[2]-.04+j/54*.10))
            tube('Stair | securing lashing',wrap,.012)
        for a,b in zip(tops[:-1],tops[1:]):
            length=(Vector(a)-Vector(b)).length;segments=max(20,int(length*20));path=[]
            for j in range(segments+1):
                t=j/segments;p=Vector(a).lerp(Vector(b),t);p.z-=.055*math.sin(t*math.pi);path.append(tuple(p))
            tube('Stair | anchored handline',path,.026)
            for strand in range(3):
                braided=[]
                for j,co in enumerate(path):
                    phase=j*.9+strand*math.tau/3;braided.append((co[0],co[1]+math.sin(phase)*.025,co[2]+math.cos(phase)*.025))
                tube('Stair | visible flax braid',braided,.0035)
    # Downhill foot ramp closes the last small transition into uneven silt.
    outer=bottom_x+1.4;tip=outer+.62
    vv=[(outer,-7.3,bottom_z),(tip,-7.3,ground(tip,-7.3)+.025),(tip,-4.7,ground(tip,-4.7)+.025),(outer,-4.7,bottom_z)]
    obj=raw('Landing | silt seated toe apron',vv,[(0,1,2,3)],woods[4],uvs=[(0,0),(0,1),(1,1),(1,0)])
    so=obj.modifiers.new('Toe timber thickness','SOLIDIFY');so.thickness=.08

    # Re-seat retained props that were beyond the old rectangular deck's true hull boundary.
    for obj in inside.objects:
        if bpy.context.scene.get('Ark props revision',1)>=2:break
        if obj.get('ark_prop_seated'):continue
        if obj.name.startswith(('Provision chest','Folded storm linen')):
            y=obj.location.y
            shift=-.6 if 10<y<14 else (1.35 if y>14 else .5)
            obj.location.x+=shift
        if obj.name.startswith(('Empty feeding trough','Trough worn lip','Trough end')):
            obj.location.x+=-.6 if obj.location.x>0 else .6
        obj['ark_prop_seated']=True
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nav={'version':2,'deck':{'z':deck,'yMin':-20.8,'yMax':20.8,'halfWidths':[[round(-20.8+i*.4,4),round(deck_limit(-20.8+i*.4)-.08,5)] for i in range(105)]},
         'stairs':{'xTop':landing_max,'xBottom':bottom_x,'zBottom':bottom_z,'zTop':deck,'count':count,'yMin':-7.0,'yMax':-5.0},
         'landings':[{'xMin':landing_min,'xMax':landing_max,'yMin':-7.09,'yMax':-4.91,'z':deck},{'xMin':bottom_x,'xMax':outer,'yMin':-7.09,'yMax':-4.91,'z':bottom_z}],
         'toe':{'xMin':outer,'xMax':tip,'yMin':-7.09,'yMax':-4.91,'zStart':bottom_z},
         'hatch':{'x':front,'yMin':door_y[0],'yMax':door_y[1],'zMin':deck,'zMax':door_z[1]}}
    os.makedirs(os.path.join(root,'public','assets'),exist_ok=True)
    with open(os.path.join(root,'public','assets','navigation.json'),'w') as f:json.dump(nav,f,indent=2)
    bpy.context.scene['Ark structure revision']=2
    bpy.context.scene['Ark props revision']=2
    bpy.context.scene['Ark stair specification']='28 horizontal closed-riser steps; exact-height connected landings; terrain-seated bents and rope lashings.'
    bpy.context.view_layer.update()
    return nav

ARK_NAVIGATION=rebuild_ark_structure()
