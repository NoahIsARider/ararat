"""Apply native-only atmosphere tuning without rebuilding unchanged geometry."""
import bpy,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path=os.path.join(ROOT,'blender','ARARAT_The_First_Earth.blend')
bpy.ops.wm.open_mainfile(filepath=path)
fog=bpy.data.materials.get('Atmosphere | rain lifted mist')
if fog:
    for node in fog.node_tree.nodes:
        if node.type=='PRINCIPLED_VOLUME':node.inputs['Density'].default_value=.0008
cloud=bpy.data.materials.get('Atmosphere | torn storm deck')
if cloud:
    for node in cloud.node_tree.nodes:
        if node.type=='MATH' and node.operation=='MULTIPLY' and not node.inputs[1].is_linked:
            node.inputs[1].default_value=.06
scene=bpy.context.scene
if hasattr(scene.cycles,'volume_step_rate'):scene.cycles.volume_step_rate=2
if hasattr(scene.cycles,'volume_max_steps'):scene.cycles.volume_max_steps=256
bpy.ops.wm.save_as_mainfile(filepath=path)
print('NATIVE_ATMOSPHERE_SAVED',flush=True)
