extends "restaurant_view_native.gd"

# Validation-only isolation: actual feedback methods, sprites suppressed to expose strokes.
func sprite(_identity: String, _base: Vector2, _clip := "static", _direction := "S", _seconds := 0.0, _tile_pixels := -1.0, _tint := Color.WHITE) -> void:
	pass
func _probe_draw() -> void:
	var base := cell_base(2,4)
	if state.get("_probe_kind", "clock") == "clock":
		_chef_at({"held_dish":{"recipe_id":"salmon_nigiri"},"visual_phase":"hold","active":true},base,cell)
	else:
		_feedback_at({"phase":"waiting","preference_phase":"active","preference_phase_elapsed":2.0,"preference_progress":state.get("_probe_progress",1.0)},base,cell)

func _draw() -> void:
	if _native_world_clone or not native_composition_enabled:
		_probe_draw()
