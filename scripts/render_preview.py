"""Fast native preview; the saved source project keeps its Cycles settings."""
import bpy, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','ARARAT_The_First_Earth.blend'))
scene=bpy.context.scene
try:
    scene.render.engine='BLENDER_EEVEE'
except TypeError as error:
    print(error,flush=True)
    raise
scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.render.filepath=os.path.join(ROOT,'artifacts','blender-preview.png')
print('NATIVE_PREVIEW_RENDERING',flush=True)
bpy.ops.render.render(write_still=True)
print('NATIVE_PREVIEW_SAVED',flush=True)
