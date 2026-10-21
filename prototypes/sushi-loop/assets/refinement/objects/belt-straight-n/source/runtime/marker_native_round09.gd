extends "restaurant_view_native.gd"
# Validation-only isolation, through the actual production native-world helper.
func _draw() -> void:
	if _native_world_clone or not native_composition_enabled:
		_editor_ground()
		_editor_ghost()
