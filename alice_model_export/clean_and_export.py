import bpy
import bmesh
from pathlib import Path

BASE = Path("/tmp/file_attachments/alice_3d_model_export_package/alice_model_export")
OUT = BASE / 'out'
OUT.mkdir(exist_ok=True)

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import base model
SRC_GLB = BASE / 'free_human_base_meshes_for_sculpting.glb'
bpy.ops.import_scene.gltf(filepath=str(SRC_GLB))

print("\n--- Processing Female Model ---")
female_obj_name = None
for obj in bpy.context.scene.objects:
    if "Female" in obj.name and obj.type == 'MESH':
        female_obj_name = obj.name
        obj.select_set(False)
    else:
        obj.select_set(True)

# Delete unwanted objects
bpy.ops.object.delete()

if female_obj_name:
    female_obj = bpy.data.objects.get(female_obj_name)
    female_obj.name = "Alice_Base_Mesh"
    female_obj.select_set(True)
    bpy.context.view_layer.objects.active = female_obj

    # 1. Apply transforms
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 2. Cleanup Mesh (Remove doubles, fix normals)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Remove doubles (merge by distance)
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

    # Recalculate normals outside
    bpy.ops.mesh.normals_make_consistent(inside=False)

    # Clean up loose geometry
    bpy.ops.mesh.delete_loose()

    # Dissolve degenerate geometry
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Check for Non-Manifold geometry (using bmesh)
    bm = bmesh.new()
    bm.from_mesh(female_obj.data)
    non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
    print(f"Non-manifold vertices after cleanup: {len(non_manifold_verts)}")

    # Tris to quads
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.tris_convert_to_quads()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Update bmesh to check poly count
    bm.clear()
    bm.from_mesh(female_obj.data)

    # Print stats
    print(f"Verts: {len(bm.verts)}, Edges: {len(bm.edges)}, Faces: {len(bm.faces)}")
    bm.free()

    # Smooth shading
    bpy.ops.object.shade_smooth()

    # Export to out folder
    out_glb = str(OUT / 'alice_optimized_base_mesh.glb')
    bpy.ops.export_scene.gltf(
        filepath=out_glb,
        export_format='GLB',
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        use_selection=True
    )
    print(f"Exported optimized mesh to {out_glb}")
else:
    print("Could not find the female model!")
