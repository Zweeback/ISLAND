class_name MapDataParser
extends RefCounted

static func parse_geojson_hoerde(file_path: String) -> Array:
	if not FileAccess.file_exists(file_path):
		printerr("GeoJSON-Datei nicht gefunden: ", file_path)
		return []

	var file = FileAccess.open(file_path, FileAccess.READ)
	if not file:
		printerr("Konnte GeoJSON-Datei für Hörde nicht öffnen: ", file_path)
		return []

	var json_text = file.get_as_text()
	file.close()

	var json = JSON.new()
	var error = json.parse(json_text)

	if error != OK:
		printerr("JSON Parse Error: ", json.get_error_message(), " in Zeile ", json.get_error_line())
		return []

	var data = json.get_data()
	if data is Dictionary and data.has("features"):
		var features = data["features"]
		if features is Array:
			return features as Array

	return []
