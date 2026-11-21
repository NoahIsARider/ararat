import bpy, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','ARARAT_The_First_Earth.blend'))
scene=bpy.context.scene
scene.cycles.samples=24
if hasattr(scene.cycles,'volume_step_rate'):scene.cycles.volume_step_rate=4
if hasattr(scene.cycles,'volume_max_steps'):scene.cycles.volume_max_steps=128
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    gpu=False
    for d in prefs.devices:
        d.use=d.type!='CPU'
        if d.use:gpu=True
    if gpu:scene.cycles.device='GPU'
except Exception as e:print('CPU render',str(e))
scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.render.filepath=os.path.join(ROOT,'artifacts','blender-cover.png')
print('CYCLES_COVER_RENDERING',flush=True)
bpy.ops.render.render(write_still=True)
print('COVER_RENDERED')
