extends SceneTree
## Run in the isolated project prepared by validate_godot_imports.py.

var report := {
	"scope": "Godot import and AtlasTexture/SpriteFrames resource validation; no Android build or gameplay test",
	"godotVersion": Engine.get_version_info(),
	"objects": 0, "clips": 0, "frameFacingContexts": 0,
	"images": {}, "errors": [], "maximumAtlasSize": [0, 0],
}

func _initialize() -> void:
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://library.json"))
	if not manifest is Dictionary or not manifest.has("objects"):
		report.errors.append("Invalid library manifest")
		_finish()
		return
	for object in manifest.objects:
		report.objects += 1
		for clip in object.clips:
			for facing in clip.directions:
				_validate_clip(object, clip, str(facing))
	_finish()

func _validate_clip(object: Dictionary, clip: Dictionary, facing: String) -> void:
	var atlas: Dictionary = clip.directions[facing]
	var path := "res://" + str(atlas.image)
	var context := str(object.id) + "/" + str(clip.id) + "/" + facing
	var texture = ResourceLoader.load(path, "Texture2D", ResourceLoader.CACHE_MODE_IGNORE)
	if not texture is Texture2D:
		report.errors.append(context + ": texture did not import")
		return
	var size: Vector2i = texture.get_size()
	if size != Vector2i(int(atlas.atlasSize[0]), int(atlas.atlasSize[1])):
		report.errors.append(context + ": imported dimensions differ from manifest")
	if maxi(size.x, size.y) > 8192:
		report.errors.append(context + ": atlas exceeds the 8192-pixel publication cap")
	report.images[str(atlas.image)] = [size.x, size.y]
	report.maximumAtlasSize[0] = maxi(report.maximumAtlasSize[0], size.x)
	report.maximumAtlasSize[1] = maxi(report.maximumAtlasSize[1], size.y)
	var animation := SpriteFrames.new()
	animation.set_animation_speed(&"default", float(clip.fps))
	animation.set_animation_loop(&"default", bool(clip.loop))
	for index in range(atlas.rects.size()):
		var rect: Array = atlas.rects[index]
		var region := Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
		if region.position.x < 0 or region.position.y < 0 or region.end.x > size.x or region.end.y > size.y:
			report.errors.append(context + ": frame region exceeds imported texture")
		var frame := AtlasTexture.new()
		frame.atlas = texture
		frame.region = region
		animation.add_frame(&"default", frame)
	if animation.get_frame_count(&"default") != int(clip.frames):
		report.errors.append(context + ": SpriteFrames count differs from manifest")
	if int(clip.frames) > 1 and animation.get_frame_count(&"default") < 6:
		report.errors.append(context + ": fewer than six animation frames")
	report.clips += 1
	report.frameFacingContexts += animation.get_frame_count(&"default")

func _finish() -> void:
	report["passed"] = report.errors.is_empty()
	report["uniqueAtlasImages"] = report.images.size()
	var file := FileAccess.open("res://validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	print("S33_GODOT_ATLAS_VALIDATION ", JSON.stringify({
		"passed": report.passed, "objects": report.objects,
		"atlasImages": report.uniqueAtlasImages,
		"frameFacingContexts": report.frameFacingContexts,
		"errors": report.errors,
	}))
	quit(0 if report.passed else 1)
