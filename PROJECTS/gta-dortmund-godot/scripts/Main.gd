extends Node3D

class_name WorldStreamingManager

@export var player_path: NodePath
@export var sector_size: float = 100.0
@export var view_distance_sectors: int = 2

var player: Node3D
var active_sectors: Dictionary = {} # Key: Vector2i, Value: Node
var loading_sectors: Array[Vector2i] = []
var metrics: Dictionary = {}

signal sector_loaded(sector_coord: Vector2i)
signal sector_unloaded(sector_coord: Vector2i)

func _ready() -> void:
	if not player_path.is_empty():
		player = get_node(player_path)

	if player:
		update_streaming_sectors(player.global_position)

var last_sector_coord: Vector2i = Vector2i(999999, 999999)

func _process(_delta: float) -> void:
	if not player:
		return
	var current_sector = get_sector_coord(player.global_position)
	if current_sector != last_sector_coord:
		last_sector_coord = current_sector
		update_streaming_sectors(player.global_position)

	_check_loading_sectors()

func _check_loading_sectors() -> void:
	var to_remove: Array[Vector2i] = []
	for sector_coord in loading_sectors:
		var scene_path = "res://assets/import/hoerde/sectors/sector_%d_%d.tscn" % [sector_coord.x, sector_coord.y]
		var status = ResourceLoader.load_threaded_get_status(scene_path)
		if status == ResourceLoader.THREAD_LOAD_LOADED:
			var packed_scene = ResourceLoader.load_threaded_get(scene_path) as PackedScene
			var sector_instance = packed_scene.instantiate()
			add_child(sector_instance)
			sector_instance.global_position = Vector3(sector_coord.x * sector_size, 0, sector_coord.y * sector_size)
			active_sectors[sector_coord] = sector_instance
			to_remove.append(sector_coord)
			emit_signal("sector_loaded", sector_coord)
			if metrics.has(sector_coord):
				_log_telemetry(sector_coord, float(Time.get_ticks_msec()) - float(metrics[sector_coord]))
		elif status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			to_remove.append(sector_coord)

	for sector_coord in to_remove:
		loading_sectors.erase(sector_coord)

func get_sector_coord(world_pos: Vector3) -> Vector2i:
	return Vector2i(
		floor(world_pos.x / sector_size),
		floor(world_pos.z / sector_size)
	)

func update_streaming_sectors(player_pos: Vector3) -> void:
	var center_sector = get_sector_coord(player_pos)
	var needed_sectors: Array[Vector2i] = []

	for x in range(-view_distance_sectors, view_distance_sectors + 1):
		for z in range(-view_distance_sectors, view_distance_sectors + 1):
			var sector_coord = center_sector + Vector2i(x, z)
			needed_sectors.append(sector_coord)

			if not active_sectors.has(sector_coord) and not loading_sectors.has(sector_coord):
				_load_sector_async(sector_coord)

	var existing_keys = active_sectors.keys()
	for sector_coord in existing_keys:
		if not sector_coord in needed_sectors:
			_unload_sector(sector_coord)

func _load_sector_async(sector_coord: Vector2i) -> void:
	loading_sectors.append(sector_coord)
	var start_time = Time.get_ticks_msec()
	metrics[sector_coord] = start_time

	var scene_path = "res://assets/import/hoerde/sectors/sector_%d_%d.tscn" % [sector_coord.x, sector_coord.y]

	if not ResourceLoader.exists(scene_path):
		_instantiate_placeholder_sector(sector_coord)
		loading_sectors.erase(sector_coord)
		_log_telemetry(sector_coord, float(Time.get_ticks_msec() - start_time))
		return

	ResourceLoader.load_threaded_request(scene_path)

func _instantiate_placeholder_sector(sector_coord: Vector2i) -> void:
	var mesh_instance = MeshInstance3D.new()
	var box = BoxMesh.new()
	box.size = Vector3(sector_size, 2.0, sector_size)
	mesh_instance.mesh = box

	add_child(mesh_instance)
	mesh_instance.global_position = Vector3(sector_coord.x * sector_size + sector_size/2, 0, sector_coord.y * sector_size + sector_size/2)
	active_sectors[sector_coord] = mesh_instance

func _unload_sector(sector_coord: Vector2i) -> void:
	if active_sectors.has(sector_coord):
		var node = active_sectors[sector_coord]
		node.queue_free()
		active_sectors.erase(sector_coord)
		emit_signal("sector_unloaded", sector_coord)

func _log_telemetry(coord: Vector2i, time_ms: float) -> void:
	metrics[coord] = time_ms
	if time_ms > 50.0:
		print("Warnung: Sektor ", coord, " benötigte ", time_ms, "ms (Latenz-Spitze)")
