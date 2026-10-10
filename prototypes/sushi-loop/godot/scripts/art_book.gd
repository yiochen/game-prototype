extends RefCounted
## One asset library serves the playable room and native component review.

const MANIFEST := "res://assets/production/manifest.json"
const ANIMATIONS := "res://assets/production/animations.json"
var textures: Dictionary = {}
var metadata: Dictionary = {}
var animations: Dictionary = {}

func reload() -> void:
	textures.clear()
	metadata.clear()
	animations.clear()
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
	if FileAccess.file_exists(ANIMATIONS):
		var clips: Variant = JSON.parse_string(FileAccess.get_file_as_string(ANIMATIONS))
		if clips is Dictionary:
			animations = clips

func get_texture(key: String) -> Texture2D:
	return textures.get(key)

func animation_frame(clip: String, seconds: float, phase := 0.0) -> String:
	var data: Dictionary = animations.get(clip, {})
	var frames: Array = data.get("frames", [])
	if frames.is_empty():
		return clip
	var index := int(floor(maxf(0.0, seconds) * float(data.get("fps", 8.0)) + phase)) % frames.size()
	return str(frames[index])

func fit(key: String, base: Vector2, maximum: Vector2) -> Rect2:
	var texture := get_texture(key)
	if texture == null:
		return Rect2()
	var native := texture.get_size()
	var reference: Array = metadata.get(key, {}).get("scale_reference", [native.x, native.y])
	var scale_factor := minf(maximum.x / float(reference[0]), maximum.y / float(reference[1]))
	var dimensions := native * scale_factor
	var anchor: Array = metadata.get(key, {}).get("anchor", [0.5, 1.0])
	return Rect2(base - Vector2(float(anchor[0]), float(anchor[1])) * dimensions, dimensions)
