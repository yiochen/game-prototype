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
const EXPANSION_MANIFEST := "res://assets/expansion/manifest.json"
const EXPANSION_DIRECTORY := "res://assets/expansion/"
## #61 cash piles, tip jar and tip feedback, baked by tools/bake_tip_art.gd.
const TIPS_MANIFEST := "res://assets/tips/manifest.json"
const TIPS_DIRECTORY := "res://assets/tips/"
const PICK_ALPHA := 0.1
## Android builds trim, downscale and repack every frame (tools/pack_runtime_sprites.gd)
## and describe the result here. Approved manifests stay byte-identical.
const RUNTIME_PACK := "runtime_pack.json"
## Decoded RGBA bytes kept for recently drawn atlases. Reloading an atlas is a
## synchronous decode and upload, so clips that end and replay must stay resident.
const CACHE_BUDGET_BYTES := 512 * 1024 * 1024
static var _pack_cache: Dictionary = {}
var objects: Dictionary = {}
var sources: Dictionary = {}
var used_sources: Dictionary = {}
var source_bytes: Dictionary = {}
var last_used: Dictionary = {}
var metadata: Dictionary = {}
var cell_size := 128.0
var revision := 0
var alpha_masks: Dictionary = {}
var budget_bytes := CACHE_BUDGET_BYTES
## Loads per atlas path; a repeat within budget means an atlas was dropped early.
var load_counts: Dictionary = {}
var frame_serial := 0
## Atlas pixels per authored source pixel; 1.0 when sprites are unpacked.
var texture_scale := 1.0
var packs: Dictionary = {}
## Registration and clip records are immutable manifest data, read for every
## drawn sprite.
var _registrations: Dictionary = {}
var _clips: Dictionary = {}

func reload() -> void:
	revision += 1
	alpha_masks.clear()
	used_sources.clear()
	objects.clear()
	sources.clear()
	source_bytes.clear()
	last_used.clear()
	metadata.clear()
	packs.clear()
	_registrations.clear()
	_clips.clear()
	texture_scale = 1.0
	for directory in [DIRECTORY, MEAL_DIRECTORY, CHEF_DIRECTORY, FEEDBACK_DIRECTORY, EXPANSION_DIRECTORY, TIPS_DIRECTORY]:
		_load_pack(directory)
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
	var expansion: Variant = JSON.parse_string(FileAccess.get_file_as_string(EXPANSION_MANIFEST))
	if expansion is Dictionary:
		for identity in expansion.get("objects",{}):
			if not objects.has(identity): objects[identity] = expansion.objects[identity].duplicate(true)
	_merge_variants(EXPANSION_MANIFEST,EXPANSION_DIRECTORY)
	var tips: Variant = JSON.parse_string(FileAccess.get_file_as_string(TIPS_MANIFEST))
	if tips is Dictionary:
		for identity in tips.get("objects", {}):
			if not objects.has(identity): objects[identity] = tips.objects[identity].duplicate(true)
	_merge_variants(TIPS_MANIFEST, TIPS_DIRECTORY)

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

func _load_pack(directory: String) -> void:
	var path := directory + RUNTIME_PACK
	if not _pack_cache.has(path):
		var parsed := {}
		if FileAccess.file_exists(path):
			var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
			if data is Dictionary:
				parsed.scale = float(data.get("scale", 1.0))
				parsed.images = {}
				for image in data.get("images", {}):
					var frames := {}
					var records: Dictionary = data.images[image].frames
					for key in records:
						var r: Array = records[key]
						var frame := Vector2(float(r[8]), float(r[9]))
						frames[key] = [Rect2(r[0], r[1], r[2], r[3]), Rect2(Vector2(r[4], r[5]) / frame, Vector2(r[6], r[7]) / frame)]
					parsed.images[directory + str(image)] = frames
		_pack_cache[path] = parsed
	var pack: Dictionary = _pack_cache[path]
	if pack.is_empty(): return
	packs.merge(pack.images)
	if directory == DIRECTORY: texture_scale = pack.scale

func begin_frame() -> void:
	frame_serial += 1
	used_sources.clear()

func end_frame() -> void:
	# Keep every atlas drawn this frame, then release the least recently drawn
	# ones until the decoded set fits the budget.
	var total := 0
	for path in sources: total += int(source_bytes.get(path, 0))
	if total > budget_bytes:
		var order: Array = sources.keys()
		order.sort_custom(func(a, b): return int(last_used.get(a, 0)) < int(last_used.get(b, 0)))
		for path in order:
			if total <= budget_bytes: break
			if used_sources.has(path): continue
			total -= int(source_bytes.get(path, 0))
			sources.erase(path)
			source_bytes.erase(path)
			last_used.erase(path)
	for path in alpha_masks.keys():
		if not sources.has(path): alpha_masks.erase(path)

func clip_data(identity: String, clip := "static") -> Dictionary:
	var clips: Dictionary = objects.get(identity, {}).get("clips", {})
	if clips.has(clip):
		return clips[clip]
	return clips.values()[0] if not clips.is_empty() else {}

func direction_data(identity: String, clip := "static", direction := "S") -> Dictionary:
	var directions: Dictionary = clip_data(identity, clip).get("directions", {})
	return directions.get(direction, directions.get("S", {}))

func registration(identity: String, clip := "static", direction := "S") -> Dictionary:
	var key := identity + "|" + clip + "|" + direction
	if _registrations.has(key): return _registrations[key]
	var object: Dictionary = objects.get(identity, {})
	var action := clip_data(identity, clip)
	var entry := direction_data(identity, clip, direction)
	var result := {
		"frame_size": entry.get("frameSize", action.get("frameSize", object.get("frameSize", [192, 320]))),
		"root": entry.get("root", action.get("root", object.get("root", [96, 248]))),
		"source_scale": float(entry.get("sourceScale", action.get("sourceScale", object.get("sourceScale", 2)))),
	}
	result.make_read_only()
	_registrations[key] = result
	return result

func _clip_record(identity: String, clip: String, direction: String) -> Dictionary:
	var key := identity + "|" + clip + "|" + direction
	if _clips.has(key): return _clips[key]
	var action := clip_data(identity, clip)
	var entry := direction_data(identity, clip, direction)
	var record := {}
	if not entry.is_empty():
		var path: String = str(entry.get("_directory", DIRECTORY)) + str(entry.image)
		# A packed frame is the opaque part of the whole frame; trim places it
		# within the registered frame rectangle in normalized units.
		var regions: Array[Rect2] = []
		var trims: Array[Rect2] = []
		var packed_frames: Dictionary = packs.get(path, {})
		for rect in entry.rects:
			var packed: Array = packed_frames.get("%d,%d,%d,%d" % [rect[0], rect[1], rect[2], rect[3]], [])
			regions.append(packed[0] if not packed.is_empty() else Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])))
			trims.append(packed[1] if not packed.is_empty() else Rect2(0, 0, 1, 1))
		record = {"path": path, "count": int(entry.get("frames", action.get("frames", 1))), "fps": float(action.get("fps", 12)),
			"loop": action.get("loop", true) != false, "regions": regions, "trims": trims}
	_clips[key] = record
	return record

func frame_data(identity: String, clip := "static", direction := "S", seconds := 0.0) -> Dictionary:
	var record := _clip_record(identity, clip, direction)
	if record.is_empty():
		return {}
	var path: String = record.path
	used_sources[path] = true
	last_used[path] = frame_serial
	if not sources.has(path):
		if not ResourceLoader.exists(path):
			push_error("Missing approved catalog texture: " + path)
			return {}
		var texture: Texture2D = ResourceLoader.load(path, "Texture2D", ResourceLoader.CACHE_MODE_IGNORE)
		load_counts[path] = int(load_counts.get(path, 0)) + 1
		sources[path] = texture
		source_bytes[path] = texture.get_width() * texture.get_height() * 4 if texture != null else 0
	var count: int = record.count
	var index := maxi(0, int(floor(maxf(0.0, seconds) * float(record.fps) + 0.0000001)))
	index = index % count if record.loop else mini(index, count - 1)
	var result := registration(identity, clip, direction).duplicate()
	result.merge({"texture": sources[path], "source_path": path, "region": record.regions[index], "trim": record.trims[index], "frame": index, "frames": count})
	return result

func trimmed_rect(frame: Dictionary, registered: Rect2) -> Rect2:
	var trim: Rect2 = frame.get("trim", Rect2(0, 0, 1, 1))
	return Rect2(registered.position + trim.position * registered.size, trim.size * registered.size)

func frame_has_ink(frame: Dictionary, atlas_pixel: Vector2) -> bool:
	# Keep one compact CPU alpha mask beside each currently loaded atlas. The
	# image is read/decompressed once, not copied or downloaded for each touch.
	var texture: Texture2D = frame.get("texture")
	if texture == null: return false
	var path := str(frame.get("source_path", "texture:%s" % texture.get_instance_id()))
	var cached: Dictionary = alpha_masks.get(path, {})
	if cached.get("texture_id", -1) != texture.get_instance_id():
		var pixels := texture.get_image()
		if pixels == null: return false
		if pixels.is_compressed() and pixels.decompress() != OK: return false
		var mask := BitMap.new()
		mask.create_from_image_alpha(pixels, PICK_ALPHA)
		cached = {"texture_id": texture.get_instance_id(), "mask": mask}
		alpha_masks[path] = cached
	var mask: BitMap = cached.mask
	var point := Vector2i(floori(atlas_pixel.x), floori(atlas_pixel.y))
	var dimensions := mask.get_size()
	if point.x < 0 or point.y < 0 or point.x >= dimensions.x or point.y >= dimensions.y: return false
	return mask.get_bitv(point)

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
	var trim: Rect2 = data.trim
	var full: Vector2 = data.region.size / trim.size
	texture.margin = Rect2(trim.position * full, full - data.region.size)
	texture.filter_clip = true
	return texture

func socket(identity: String, name: String, direction := "S") -> Vector2:
	var sockets: Dictionary = objects.get(identity, {}).get("sockets", {}).get(direction, {})
	var value: Variant = sockets.get(name, [0, 0])
	if value is Dictionary:
		value = value.get("position", [0, 0])
	return Vector2(float(value[0]), float(value[1]))
