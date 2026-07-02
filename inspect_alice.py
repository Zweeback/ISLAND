import bpy
import bmesh
bpy.ops.import_scene.gltf(filepath="/app/alice_model_export/free_human_base_meshes_for_sculpting.glb")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print(f"Object: {obj.name}, Verts: {len(obj.data.vertices)}, Polys: {len(obj.data.polygons)}")
