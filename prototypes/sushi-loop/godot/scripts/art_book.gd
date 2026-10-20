extends RefCounted
## One approved #33 registration contract serves the game and native gallery.
## Full-frame scale comes from the 128px cell, never the silhouette or pose.

const MANIFEST := "res://assets/catalog/manifest.json"
const DIRECTORY := "res://assets/catalog/"
const MEAL_MANIFEST := "res://assets/recipe-variants/manifest.json"
const MEAL_DIRECTORY := "res://assets/recipe-variants/"
const CHEF_MANIFEST := "res://assets/chef-variants/manifest.json"
const CHEF_DIRECTORY := "res://assets/chef-variants/"
const FEEDBACK_MANIFEST := "res://assets/feedback-variants/manifest.json"
const FEEDBACK_DIRECTORY := "res://assets/feedback-variants/"
var objects: Dictionary = {}
var sources: Dictionary = {}
var used_sources: Dictionary = {}
var metadata: Dictionary = {}
var cell_size := 128.0

func reload() -> void:
	objects.clear()
	sources.clear()
	metadata.clear()
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if data is Dictionary:
		objects = data.get("objects", {})
		metadata = objects
		cell_size = float(data.get("cellSize", 128))
	# Recipe-specific native clips extend the approved objects; base captures
	# and registration remain untouched and separately hash-verifiable.
	_merge_variants(MEAL_MANIFEST, MEAL_DIRECTORY)
	_merge_variants(CHEF_MANIFEST, CHEF_DIRECTORY)
	_merge_variants(FEEDBACK_MANIFEST, FEEDBACK_DIRECTORY)

func _merge_variants(path: String, directory: String) -> void:
	var variants: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not variants is Dictionary:
		return
	for identity in variants.get("objects", {}):
		if not objects.has(identity):
			continue
		var clips: Dictionary = variants.objects[identity].get("clips", {})
		for clip in clips:
			var record: Dictionary = clips[clip].duplicate(true)
			for entry in record.directions.values():
				entry["_directory"] = directory
			objects[identity].clips[clip] = record

func begin_frame() -> void:
	used_sources.clear()

func end_frame() -> void:
	# Release old action atlases after drawing. Mobile only keeps the actions
	# actually visible, rather than every facing of the full character library.
	for path in sources.keys():
		if not used_sources.has(path):
			sources.erase(path)

func clip_data(identity: String, clip := "static") -> Dictionary:
	var clips: Dictionary = objects.get(identity, {}).get("clips", {})
	if clips.has(clip):
		return clips[clip]
	return clips.values()[0] if not clips.is_empty() else {}

func direction_data(identity: String, clip := "static", direction := "S") -> Dictionary:
	var directions: Dictionary = clip_data(identity, clip).get("directions", {})
	return directions.get(direction, directions.get("S", {}))

func registration(identity: String, clip := "static", direction := "S") -> Dictionary:
	var object: Dictionary = objects.get(identity, {})
	var action := clip_data(identity, clip)
	var entry := direction_data(identity, clip, direction)
	return {
		"frame_size": entry.get("frameSize", action.get("frameSize", object.get("frameSize", [192, 320]))),
		"root": entry.get("root", action.get("root", object.get("root", [96, 248]))),
		"source_scale": float(entry.get("sourceScale", action.get("sourceScale", object.get("sourceScale", 2)))),
	}

func frame_data(identity: String, clip := "static", direction := "S", seconds := 0.0) -> Dictionary:
	var action := clip_data(identity, clip)
	var entry := direction_data(identity, clip, direction)
	if entry.is_empty():
		return {}
	var path: String = str(entry.get("_directory", DIRECTORY)) + str(entry.image)
	used_sources[path] = true
	if not sources.has(path):
		if not ResourceLoader.exists(path):
			push_error("Missing approved catalog texture: " + path)
			return {}
		sources[path] = ResourceLoader.load(path, "Texture2D", ResourceLoader.CACHE_MODE_IGNORE)
	var count := int(entry.get("frames", action.get("frames", 1)))
	var index := maxi(0, int(floor(maxf(0.0, seconds) * float(action.get("fps", 12)) + 0.0000001)))
	index = mini(index, count - 1) if action.get("loop", true) == false else index % count
	var rect: Array = entry.rects[index]
	var result := registration(identity, clip, direction)
	result.merge({"texture": sources[path], "region": Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])), "frame": index, "frames": count})
	return result

func registered_rect(identity: String, base: Vector2, tile_pixels: float, clip := "static", direction := "S") -> Rect2:
	var data := registration(identity, clip, direction)
	var root: Array = data.root
	var bounds: Array = data.frame_size
	var scale_factor := tile_pixels / cell_size
	return Rect2(base - Vector2(float(root[0]), float(root[1])) * scale_factor, Vector2(float(bounds[0]), float(bounds[1])) * scale_factor)

func get_texture(identity: String, clip := "static", direction := "S", seconds := 0.0) -> Texture2D:
	var data := frame_data(identity, clip, direction, seconds)
	if data.is_empty():
		return null
	var texture := AtlasTexture.new()
	texture.atlas = data.texture
	texture.region = data.region
	texture.filter_clip = true
	return texture

func socket(identity: String, name: String, direction := "S") -> Vector2:
	var sockets: Dictionary = objects.get(identity, {}).get("sockets", {}).get(direction, {})
	var value: Variant = sockets.get(name, [0, 0])
	if value is Dictionary:
		value = value.get("position", [0, 0])
	return Vector2(float(value[0]), float(value[1]))
