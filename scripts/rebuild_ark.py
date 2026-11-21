"""Incremental structural rebuild: keep the approved landscape and its vegetation."""
import bpy,os,json,bmesh
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path=os.path.join(ROOT,'blender','ARARAT_The_First_Earth.blend')
bpy.ops.wm.open_mainfile(filepath=path)
exec(compile(open(os.path.join(ROOT,'scripts','ark_structure.py'),encoding='utf-8').read(),'ark_structure.py','exec'),globals())
exec(compile(open(os.path.join(ROOT,'scripts','exile_boat.py'),encoding='utf-8').read(),'exile_boat.py','exec'),globals())
scene=bpy.context.scene
depsgraph=bpy.context.evaluated_depsgraph_get()
skin=bpy.data.objects.get('Ark | sealed bilge and transom skin')
ev=skin.evaluated_get(depsgraph);data=ev.to_mesh();bm=bmesh.new();bm.from_mesh(data)
boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
bm.free();ev.to_mesh_clear()
treads=sorted([o for o in scene.objects if o.name.startswith('Stair | horizontal tread')],key=lambda o:o['tread_index'])
nav=ARK_NAVIGATION;s=nav['stairs'];rise=(s['zTop']-s['zBottom'])/s['count']
assert len(treads)==28
assert all(abs(o.rotation_euler.y)<1e-6 for o in treads)
assert abs(treads[-1]['top_elevation']-nav['deck']['z'])<1e-6
assert nonmanifold==0,('The sealed hull skin must be manifold after solidifying',boundary,nonmanifold)
for tread in treads:
    top=max(tread.data.polygons,key=lambda p:sum(tread.data.vertices[v].co.z for v in p.vertices)/len(p.vertices))
    assert top.normal.z>.99,('Tread face normals must point outwards',tread.name)
pads=[o for o in scene.objects if o.name.startswith('Stair | mud seated bearing pad')]
assert len(pads)==10
for pad in pads:
    zs=[(pad.matrix_world@__import__('mathutils').Vector(c)).z for c in pad.bound_box]
    assert min(zs)<=pad['ground_elevation']<=max(zs),('Bearing pad does not intersect its sampled ground',pad.name)
report={'revision':2,'sealedHullSkin':{'boundaryEdges':boundary,'nonManifoldEdges':nonmanifold},'stairs':{'count':len(treads),'rise':rise,'going':(s['xBottom']-s['xTop'])/s['count'],'horizontal':True,'topMatchesDeck':True,'outwardTreadNormals':True,'groundedPads':len(pads)},'navigation':nav}
os.makedirs(os.path.join(ROOT,'artifacts'),exist_ok=True)
with open(os.path.join(ROOT,'artifacts','structure-verification.json'),'w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=path)
for obj in scene.objects:obj.select_set(obj.type in {'MESH','CURVE'} and not obj.name.startswith('Atmosphere'))
# Unsupported native-only procedural bump is omitted from glTF, as in the full build.
for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type=='BSDF_PRINCIPLED':
                for link in list(node.inputs['Normal'].links):
                    if link.from_node.type=='BUMP':mat.node_tree.links.remove(link)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'public','assets','ararat.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
print('STRUCTURE_REBUILT_AND_VERIFIED',json.dumps(report['stairs']),flush=True)
