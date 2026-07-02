import bpy
import bmesh

bpy.ops.import_scene.gltf(filepath="/tmp/file_attachments/alice_3d_model_export_package/alice_model_export/free_human_base_meshes_for_sculpting.glb")

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print(f"Object: {obj.name}, Verts: {len(obj.data.vertices)}, Polys: {len(obj.data.polygons)}")

        # Check for non-manifold, loose, etc.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        print(f"  After remove doubles: {len(bm.verts)}")

        non_manifold = [v for v in bm.verts if not v.is_manifold]
        print(f"  Non-manifold verts: {len(non_manifold)}")

        bm.free()
