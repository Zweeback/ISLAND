import bpy
from pathlib import Path

# Blender 3.6 script: import base mesh, normalize scene, export FBX + glTF/GLB.
# Usage: blender -b --python run_blender_export.py
BASE = Path(__file__).resolve().parent
OUT = BASE / 'out'
OUT.mkdir(exist_ok=True)

SRC_GLB = BASE / 'free_human_base_meshes_for_sculpting.glb'
SRC_FBX = BASE / 'Sculpting Human Base Meshes.fbx'

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

if SRC_GLB.exists():
    bpy.ops.import_scene.gltf(filepath=str(SRC_GLB))
elif SRC_FBX.exists():
    bpy.ops.import_scene.fbx(filepath=str(SRC_FBX))
else:
    raise FileNotFoundError('No source GLB or FBX found next to script.')

# Clean transforms: keep geometry, apply scale/rotation for game-engine friendliness.
for obj in bpy.context.scene.objects:
    obj.select_set(obj.type == 'MESH')
bpy.context.view_layer.objects.active = next((o for o in bpy.context.scene.objects if o.type == 'MESH'), None)
if bpy.context.view_layer.objects.active:
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Export both requested interchange formats.
bpy.ops.export_scene.fbx(
    filepath=str(OUT / 'alice_base_mesh.fbx'),
    use_selection=False,
    apply_unit_scale=True,
    bake_space_transform=False,
    object_types={'MESH', 'ARMATURE'},
    add_leaf_bones=False,
    path_mode='AUTO'
)

bpy.ops.export_scene.gltf(
    filepath=str(OUT / 'alice_base_mesh.gltf'),
    export_format='GLTF_SEPARATE',
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT'
)

bpy.ops.export_scene.gltf(
    filepath=str(OUT / 'alice_base_mesh.glb'),
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT'
)
