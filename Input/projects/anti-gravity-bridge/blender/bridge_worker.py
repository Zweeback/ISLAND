import bpy
import json
import sys
from pathlib import Path

ALLOWED_COMMANDS = {
    "create_cube",
    "create_uv_sphere",
    "export_scene_glb",
    "clear_scene",
}

def clear_scene():
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')
    # Select all meshes and objects to clear
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_cube(scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.scale = scale
    return obj.name

def create_uv_sphere(radius=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius)
    obj = bpy.context.active_object
    return obj.name

def export_scene_glb(output_path: str):
    # Ensure parent dir exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB'
    )
    return output_path

def dispatch(cmd: dict):
    command = cmd.get("command")
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"command_not_allowed: {command}")

    if command == "clear_scene":
        clear_scene()
        return {"ok": True}

    if command == "create_cube":
        scale = tuple(cmd.get("scale", [1, 1, 1]))
        return {"ok": True, "object": create_cube(scale)}

    if command == "create_uv_sphere":
        radius = float(cmd.get("radius", 1.0))
        return {"ok": True, "object": create_uv_sphere(radius)}

    if command == "export_scene_glb":
        return {"ok": True, "path": export_scene_glb(cmd["output_path"])}

    raise ValueError("unhandled_command")

def main():
    if "--" not in sys.argv:
        raise SystemExit("Expected JSON command file after --")
    idx = sys.argv.index("--")
    cmd_file = Path(sys.argv[idx + 1])
    cmd = json.loads(cmd_file.read_text(encoding="utf-8"))
    result = dispatch(cmd)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
