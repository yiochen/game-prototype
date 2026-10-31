extends Node
## Adapts the existing renderer without changing render_plan, sprite registration,
## overlays, state, input conversion or owner/picking records.
const NativePixelComposer = preload("native_pixel_compositor.gd")
var source_view: Control
var native_view: Control
var native_pipeline: Node
var surface: Control

func initialize(view: Control) -> void:
	source_view = view
	native_view = view.get_script().new()
	native_view.native_composition_enabled = false
	native_view._native_world_clone = true
	native_view._native_world_controller = self
	# One ArtBook/visible-atlas cache serves rendering and the untouched hit pass.
	native_view.art = view.art
	native_pipeline = NativePixelComposer.new()
	add_child(native_pipeline)
	native_pipeline.initialize(native_view, Vector2(16, 16))
	native_view.set_process(false)
	surface = native_pipeline.make_surface(source_view, Rect2(), 1.0)
	surface.hide()
	sync()

func sync() -> void:
	if source_view.show_gallery or not source_view.is_visible_in_tree() or source_view.portrait.size.x <= 0.0:
		surface.hide()
		native_pipeline.set_active(false)
		if native_view._ground_shadows != null:
			native_view._ground_shadows.set_active(false)
		return
	var native_factor: float = NativePixelComposer.NATIVE_CELL / source_view.cell
	var screen_transform: Transform2D = source_view.get_viewport_transform() * source_view.get_global_transform()
	var screen_scale := minf(screen_transform.x.length(), screen_transform.y.length())
	native_pipeline.set_presentation_pixel_scale(screen_scale / native_factor)
	native_pipeline.set_active(true)
	native_view._native_screen_pixel_scale = native_factor
	# Crop only the visible portrait. Landscape letterboxes never allocate GPU
	# targets. Keep the float content extent; allocation padding is clipped.
	native_view.size = source_view.portrait.size * native_factor
	native_view.safe_top = source_view.safe_top * native_factor
	native_view.dish_flights = source_view.dish_flights
	native_view.recipe_shakes = source_view.recipe_shakes
	native_view.state = source_view.state
	native_view.time = source_view.time
	native_view.sale_pops = source_view.sale_pops
	native_view.reduced_motion = source_view.reduced_motion
	native_view.ground_shadows_enabled = source_view.ground_shadows_enabled
	native_view.editor_preview = source_view.editor_preview
	native_view.editor_selection_alpha = source_view.editor_selection_alpha
	native_view.clearance_selected = source_view.clearance_selected
	native_view.clearance_removals = source_view.clearance_removals
	native_view.dock_reveal_started = source_view.dock_reveal_started
	native_view.show_gallery = false
	# Transform the authoritative layout once. Re-running its aspect-ratio min()
	# at float native dimensions can turn a256px cell into255.99998px.
	native_view.portrait = Rect2(Vector2.ZERO, native_view.size)
	native_view.cell = NativePixelComposer.NATIVE_CELL
	native_view.sky_height = source_view.sky_height * native_factor
	native_view.floor_origin = (source_view.floor_origin - source_view.portrait.position) * native_factor
	native_pipeline.resize_native(native_view.size)
	var camera: Dictionary = source_view.state.get("camera", {})
	var camera_cells := Vector2(float(camera.get("x", 0)), float(camera.get("y", 0)))
	native_pipeline.set_grid_origin(native_view.floor_origin - camera_cells * native_view.cell)
	native_pipeline.configure_surface(surface, source_view.portrait, 1.0 / native_factor)
	surface.show()
	native_view.queue_redraw()

func begin_native_frame() -> void:
	native_pipeline.begin_native_frame()

func native_sprite_texture(identity: String, texture: Texture2D) -> Texture2D:
	return native_pipeline.native_sprite_texture(identity, texture)

func end_native_frame() -> void:
	native_pipeline.end_native_frame()

func diagnostics() -> Dictionary:
	var result: Dictionary = native_pipeline.allocation_record()
	result["source_cell"] = source_view.cell
	result["native_cell_actual"] = native_view.cell
	result["native_screen_pixel_scale"] = native_view._native_screen_pixel_scale
	result["source_portrait"] = [source_view.portrait.position.x, source_view.portrait.position.y, source_view.portrait.size.x, source_view.portrait.size.y]
	result["native_floor_origin"] = [native_view.floor_origin.x, native_view.floor_origin.y]
	result["presenter_offset"] = [surface.native_offset.x, surface.native_offset.y]
	if native_view._ground_shadows != null:
		var shadow_size: Vector2i = native_view._ground_shadows.viewport.size
		result["ground_shadow_size"] = [shadow_size.x, shadow_size.y]
		result["ground_shadow_color_buffer_bytes"] = shadow_size.x * shadow_size.y * 4
		result["ground_shadow_renderer"] = "DirectionalLight3D / shadow-only geometry"
		result["ground_shadow_receiver_color_buffer_bytes"] = shadow_size.x * shadow_size.y * 4
		result["ground_shadow_batching"] = native_view._ground_shadows.diagnostics()
	return result
