extends SceneTree
const NativePixelComposer = preload("res://runtime/native_pixel_compositor.gd")
class Drawing:
	extends Node2D
	var commands: Array[Dictionary] = []
	func _draw() -> void:
		for command in commands:
			draw_texture_rect_region(command.texture, command.destination, command.region)
class Background:
	extends Node2D
	var dimensions := Vector2.ZERO
	var color := Color.TRANSPARENT
	var cell_pitch := 128
	var floor_texture: Texture2D
	func _draw() -> void:
		if color.a > 0.0: draw_rect(Rect2(Vector2.ZERO, dimensions), color)
		if floor_texture != null:
			for y in range(0, ceili(dimensions.y), cell_pitch):
				for x in range(0, ceili(dimensions.x), cell_pitch): draw_texture_rect(floor_texture, Rect2(x, y, cell_pitch, cell_pitch), false)
const BACKGROUNDS := {"game-floor-cream": Color("eed6a1")}
var captures: Array[Dictionary] = []
var outputs: Array[Dictionary] = []
var atlases: Dictionary = {}
var destination := "res://floor-outputs"
func _initialize() -> void: call_deferred("run")
func output_viewport(dimensions: Vector2i, background: Color, pitch: int) -> SubViewport:
	var viewport := SubViewport.new()
	viewport.size = dimensions
	viewport.transparent_bg = true
	viewport.disable_3d = true
	viewport.gui_disable_input = true
	viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var drawing := Background.new()
	drawing.dimensions = Vector2(dimensions)
	drawing.color = background
	drawing.cell_pitch = pitch
	drawing.floor_texture = load("res://inputs/game-floor-cream.png")
	viewport.add_child(drawing)
	return viewport
func run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://config.json"))
	DirAccess.make_dir_recursive_absolute(destination)
	var current_canvas := Drawing.new()
	var reference_canvas := Drawing.new()
	current_canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	reference_canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var current_pipeline := NativePixelComposer.new()
	var reference_pipeline := NativePixelComposer.new()
	root.add_child(current_pipeline)
	root.add_child(reference_pipeline)
	current_pipeline.initialize(current_canvas, Vector2(896, 1216))
	reference_pipeline.initialize(reference_canvas, Vector2(896, 1216))
	for identity in ["W", "N", "E", "S"]:
		for d in ["N", "E", "S", "W"]: atlases[identity + d] = load("res://inputs/%s-running-%s.png" % [identity, d])
	for pitch in [128, 55, 32]:
		var scale_factor := float(pitch) / 256.0
		var dimensions := Vector2i(ceili(896 * scale_factor), ceili(1216 * scale_factor))
		for background in BACKGROUNDS:
			for mode in ["current", "reference"]:
				var viewport := output_viewport(dimensions, BACKGROUNDS[background], pitch)
				var pipeline: Node = current_pipeline if mode == "current" else reference_pipeline
				pipeline.make_surface(viewport, Rect2(Vector2.ZERO, Vector2(dimensions)), scale_factor)
				outputs.append({"viewport": viewport, "pitch": pitch, "background": background, "mode": mode})
	for pattern in ["WWW", "WNW", "NWN", "WEW", "EWE", "WSW", "SWS"]:
		for direction in ["N", "E", "S", "W"]:
			for index_value in config.coverage[pattern]:
				var index: int = int(index_value)
				var region := Rect2((index % 24 % 6) * 384, int((index % 24) / 6) * 704, 384, 704)
				var offsets: Array = config.offsets[direction]
				var commands: Array[Dictionary] = []
				for j in range(3):
					var identity: String = pattern[j]
					var d: String = config.mapping[identity][direction]
					var point: Array = offsets[j]
					commands.append({"texture": atlases[identity + d], "destination": Rect2(point[0], point[1], 384, 704), "region": region})
				var reference_path := ProjectSettings.globalize_path(str(config.nativeReferenceDirectory)).path_join("native-%s-%s-%02d.png" % [pattern, direction, index])
				var texture := ImageTexture.create_from_image(Image.load_from_file(reference_path))
				var contexts := [Vector2.ZERO, Vector2(0.375, 0.625)]
				if index in [0, 12, 23, 24]: contexts.append_array([Vector2(0.25, 0.75), Vector2(0.875, 0.125)])
				for context_index in range(contexts.size()):
					var shift: Vector2 = contexts[context_index]
					current_pipeline.set_grid_origin(shift)
					reference_pipeline.set_grid_origin(shift)
					var moved: Array[Dictionary] = []
					for command in commands: moved.append({"texture": command.texture, "destination": Rect2(command.destination.position + shift, command.destination.size), "region": command.region})
					current_canvas.commands = moved
					current_canvas.queue_redraw()
					reference_canvas.commands = [{"texture": texture, "destination": Rect2(shift, Vector2(896, 1216)), "region": Rect2(0, 0, 896, 1216)}]
					reference_canvas.queue_redraw()
					await process_frame
					await RenderingServer.frame_post_draw
					await process_frame
					await RenderingServer.frame_post_draw
					for entry in outputs:
						var name := "%s-%s-%s-%02d-%d-c%d-%s.png" % [entry.mode, pattern, direction, index, entry.pitch, context_index, entry.background]
						var path := destination.path_join(name)
						assert(entry.viewport.get_texture().get_image().save_png(path) == OK)
						captures.append({"pattern": pattern, "direction": direction, "compatibleNDirection": config.mapping.N[direction], "compatibleEDirection": config.mapping.E[direction], "compatibleSDirection": config.mapping.S[direction], "index": index, "atlasFrame": index % 24, "phase": -7.0 * index / 24.0, "pitch": entry.pitch, "background": entry.background, "mode": entry.mode, "context": context_index, "nativeRootShift": [shift.x, shift.y], "path": ProjectSettings.globalize_path(path)})
				print("CAPTURE ", pattern, " ", direction, " ", index)
	var record := {"godot": Engine.get_version_info(), "renderer": ProjectSettings.get_setting("rendering/renderer/rendering_method"), "source": "Actual Godot GL Compatibility consumer, exact approved native compositor/reduction/presenter code. Current: independent original atlas regions. Reference: actual native Blender three-module geometry captures. Both pass through identical native nearest GPU composition, premultiplied reduction and area presentation. No raster repairs.", "pipelineAllocation": current_pipeline.allocation_record(), "captures": captures}
	var file := FileAccess.open("res://floor-render-record.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(record, "  "))
	current_pipeline.queue_free()
	reference_pipeline.queue_free()
	await process_frame
	quit()
