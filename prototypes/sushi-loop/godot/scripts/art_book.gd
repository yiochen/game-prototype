extends RefCounted
## One asset library serves the playable room and native component review.

const MANIFEST := "res://assets/production/manifest.json"
var textures: Dictionary = {}
var metadata: Dictionary = {}

func reload() -> void:
	textures.clear()
	metadata.clear()
	if not FileAccess.file_exists(MANIFEST):
		return
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if not data is Dictionary:
		return
	metadata = data.get("assets", data)
	for key in metadata:
		var entry: Variant = metadata[key]
		if not entry is Dictionary:
			continue
		var path: String = entry.get("file", "")
		if not path.begins_with("res://"):
			path = "res://assets/production/" + path
		if not ResourceLoader.exists(path):
			continue
		var source: Texture2D = load(path)
		if entry.has("region"):
			var values: Array = entry.region
			var atlas := AtlasTexture.new()
			atlas.atlas = source
			atlas.region = Rect2(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
			atlas.filter_clip = true
			textures[key] = atlas
		else:
			textures[key] = source

func get_texture(key: String) -> Texture2D:
	return textures.get(key)

func fit(key: String, base: Vector2, maximum: Vector2) -> Rect2:
	var texture := get_texture(key)
	if texture == null:
		return Rect2()
	var native := texture.get_size()
	var scale_factor := minf(maximum.x / native.x, maximum.y / native.y)
	var dimensions := native * scale_factor
	return Rect2(base - Vector2(dimensions.x * 0.5, dimensions.y), dimensions)
