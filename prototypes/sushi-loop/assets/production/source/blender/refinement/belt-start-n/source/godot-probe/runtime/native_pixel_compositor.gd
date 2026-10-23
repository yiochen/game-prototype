extends Node
## A visible-region native-pixel compositor. Contains no gameplay state, tile
## topology, picking, baked map frames, readbacks or texture copies at runtime.
const NATIVE_CELL := 256.0
const REDUCTION_LEVELS := 4
const ALLOCATION_ALIGNMENT := 16
const GUARD := Vector2(16, 16)

class ReductionCanvas:
	extends Node2D
	var source_texture: Texture2D
	var dimensions := Vector2.ZERO
	func _draw() -> void:
		if source_texture != null:
			draw_texture_rect(source_texture, Rect2(Vector2.ZERO, dimensions), false)

class Surface:
	extends Control
	var source_texture: Texture2D
	var native_dimensions := Vector2.ZERO
	var pixels_per_native := 1.0
	var native_offset := Vector2.ZERO
	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		clip_contents = true
	func _draw() -> void:
		if source_texture != null:
			draw_texture_rect(source_texture, Rect2(native_offset * pixels_per_native, native_dimensions * pixels_per_native), false)
	func configure(rect: Rect2, source_size: Vector2, scale_factor: float, offset: Vector2) -> void:
		position = rect.position
		size = rect.size
		native_dimensions = source_size
		pixels_per_native = scale_factor
		native_offset = offset
		queue_redraw()

var native_viewport: SubViewport
var reduction_viewports: Array[SubViewport] = []
var reduction_canvases: Array[Node2D] = []
var presentation_material: ShaderMaterial
var native_canvas: CanvasItem
var allocated_size := Vector2i.ZERO
var content_size := Vector2.ZERO
var grid_fraction := Vector2.ZERO
var _surfaces: Array[Control] = []
var _belt_textures: Dictionary = {}
var _used_belt_textures: Dictionary = {}

func _make_viewport() -> SubViewport:
	var result := SubViewport.new()
	result.disable_3d = true
	result.transparent_bg = true
	result.gui_disable_input = true
	result.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	result.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(result)
	return result

func initialize(canvas: CanvasItem, dimensions: Vector2) -> void:
	assert(native_viewport == null)
	native_canvas = canvas
	native_viewport = _make_viewport()
	native_viewport.add_child(canvas)
	var directory: String = get_script().resource_path.get_base_dir()
	var reduction_shader: Shader = load(directory.path_join("native_reduce2.gdshader"))
	var previous: SubViewport = native_viewport
	for _level in range(REDUCTION_LEVELS):
		var viewport := _make_viewport()
		var drawing := ReductionCanvas.new()
		drawing.source_texture = previous.get_texture()
		drawing.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		var reduction_material := ShaderMaterial.new()
		reduction_material.shader = reduction_shader
		drawing.material = reduction_material
		viewport.add_child(drawing)
		reduction_viewports.append(viewport)
		reduction_canvases.append(drawing)
		previous = viewport
	presentation_material = ShaderMaterial.new()
	presentation_material.shader = load(directory.path_join("native_present.gdshader"))
	presentation_material.set_shader_parameter("native_layer", native_viewport.get_texture())
	for level in range(REDUCTION_LEVELS):
		presentation_material.set_shader_parameter("mip_%d" % (level + 1), reduction_viewports[level].get_texture())
	resize_native(dimensions)

func resize_native(dimensions: Vector2) -> void:
	content_size = dimensions
	var desired := Vector2i(ceili((dimensions.x + GUARD.x * 2 - 0.001) / ALLOCATION_ALIGNMENT) * ALLOCATION_ALIGNMENT, ceili((dimensions.y + GUARD.y * 2 - 0.001) / ALLOCATION_ALIGNMENT) * ALLOCATION_ALIGNMENT)
	if allocated_size == desired: return
	allocated_size = desired
	native_viewport.size = allocated_size
	native_viewport.canvas_transform = Transform2D(0.0, GUARD - grid_fraction)
	var next_size := allocated_size
	for level in range(REDUCTION_LEVELS):
		next_size = Vector2i(next_size.x / 2, next_size.y / 2)
		reduction_viewports[level].size = next_size
		reduction_canvases[level].dimensions = Vector2(next_size)
		reduction_canvases[level].queue_redraw()

func make_surface(parent: Node, rect: Rect2, pixels_per_native: float) -> Control:
	var result := Surface.new()
	result.source_texture = native_viewport.get_texture()
	result.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	result.material = presentation_material
	parent.add_child(result)
	result.configure(rect, Vector2(allocated_size), pixels_per_native, grid_fraction - GUARD)
	_surfaces.append(result)
	return result

func configure_surface(surface: Control, rect: Rect2, pixels_per_native: float) -> void:
	surface.configure(rect, Vector2(allocated_size), pixels_per_native, grid_fraction - GUARD)

func set_grid_origin(origin: Vector2) -> void:
	# Common camera/floor fraction only. Never snap individual objects. Restoring
	# this offset in the presenter preserves the exact screen-space anchors.
	var fraction := origin - origin.floor()
	if grid_fraction.is_equal_approx(fraction): return
	grid_fraction = fraction
	native_viewport.canvas_transform = Transform2D(0.0, GUARD - grid_fraction)
	for surface in _surfaces:
		surface.native_offset = grid_fraction - GUARD
		surface.queue_redraw()

func set_active(active: bool) -> void:
	var mode := SubViewport.UPDATE_ALWAYS if active else SubViewport.UPDATE_DISABLED
	native_viewport.render_target_update_mode = mode
	for viewport in reduction_viewports: viewport.render_target_update_mode = mode
	if not active:
		_belt_textures.clear()
		_used_belt_textures.clear()

func begin_native_frame() -> void:
	_used_belt_textures.clear()

func native_sprite_texture(identity: String, texture: Texture2D) -> Texture2D:
	if not identity.begins_with("belt-"): return texture
	var key := texture.get_instance_id()
	_used_belt_textures[key] = true
	if not _belt_textures.has(key):
		var wrapper := CanvasTexture.new()
		wrapper.diffuse_texture = texture
		wrapper.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_belt_textures[key] = wrapper
	return _belt_textures[key]

func end_native_frame() -> void:
	for key in _belt_textures.keys():
		if not _used_belt_textures.has(key): _belt_textures.erase(key)

func allocation_record() -> Dictionary:
	var pixels := allocated_size.x * allocated_size.y
	var levels: Array = [[allocated_size.x, allocated_size.y]]
	for viewport in reduction_viewports:
		pixels += viewport.size.x * viewport.size.y
		levels.append([viewport.size.x, viewport.size.y])
	return {"native_cell": NATIVE_CELL, "content_size": [content_size.x, content_size.y], "levels": levels, "rgba8_color_buffer_bytes": pixels * 4, "phase_cache_count": 0, "runtime_readbacks": 0, "native_guard": [GUARD.x, GUARD.y], "grid_fraction": [grid_fraction.x, grid_fraction.y]}
