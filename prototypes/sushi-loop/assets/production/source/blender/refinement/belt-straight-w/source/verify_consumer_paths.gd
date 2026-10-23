extends SceneTree
func _initialize() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://config.json"))
	var captures := 0
	for pattern in config.coverage:
		for direction in ["N", "E", "S", "W"]:
			for frame in config.coverage[pattern]:
				var path := ProjectSettings.globalize_path(str(config.nativeReferenceDirectory)).path_join("native-%s-%s-%02d.png" % [pattern, direction, int(frame)])
				assert(FileAccess.file_exists(path), path)
				var image := Image.load_from_file(path)
				assert(image != null and image.get_size() == Vector2i(896, 1216), path)
				captures += 1
	assert(captures == 396)
	print("RELATIVE_NATIVE_REFERENCE_PATHS_OK ", captures)
	quit()
