extends SceneTree
const NativePixelComposer = preload("res://runtime/native_pixel_compositor.gd")
class Drawing:
	extends Node2D
	var commands: Array[Dictionary] = []
	func _draw() -> void:
		for command in commands:
			draw_texture_rect_region(command.texture, command.destination, command.region, command.get("tint", Color.WHITE))
class Background:
	extends Node2D
	var dimensions := Vector2.ZERO
	var color := Color.TRANSPARENT
	func _draw() -> void:
		if color.a > 0.0: draw_rect(Rect2(Vector2.ZERO, dimensions), color)

var config: Dictionary
var outputs: Array[Dictionary] = []
var direct: Array[Dictionary] = []
var captures: Array[Dictionary] = []
var current_canvas: Drawing
var reference_canvas: Drawing
var current_pipeline: Node
var reference_pipeline: Node
var atlases: Dictionary = {}
var destination := "res://outputs"
const BACKGROUNDS := {"transparent": Color.TRANSPARENT, "light": Color("e6e9e4"), "gray": Color("787d80"), "dark": Color("181e24")}

func _initialize() -> void:
	call_deferred("run")

func output_viewport(dimensions: Vector2i, background: Color) -> SubViewport:
	var result := SubViewport.new()
	result.size = dimensions
	result.transparent_bg = true
	result.disable_3d = true
	result.gui_disable_input = true
	result.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	result.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(result)
	var drawing := Background.new()
	drawing.dimensions = Vector2(dimensions)
	drawing.color = background
	result.add_child(drawing)
	return result

func run() -> void:
	config = JSON.parse_string(FileAccess.get_file_as_string("res://config.json"))
	DirAccess.make_dir_recursive_absolute(destination)
	current_canvas = Drawing.new()
	current_canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	reference_canvas = Drawing.new()
	reference_canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	current_pipeline = NativePixelComposer.new()
	reference_pipeline = NativePixelComposer.new()
	root.add_child(current_pipeline)
	root.add_child(reference_pipeline)
	current_pipeline.initialize(current_canvas, Vector2(896, 1216))
	reference_pipeline.initialize(reference_canvas, Vector2(896, 1216))
	for direction in ["N", "E", "S", "W"]:
		atlases[direction] = load("res://inputs/running-%s.png" % direction)
	for pitch in [128, 55, 32]:
		var scale_factor := float(pitch) / 256.0
		var dimensions := Vector2i(ceili(896 * scale_factor), ceili(1216 * scale_factor))
		for background in BACKGROUNDS:
			for mode in ["current", "reference"]:
				var viewport := output_viewport(dimensions, BACKGROUNDS[background])
				var pipeline: Node = current_pipeline if mode == "current" else reference_pipeline
				pipeline.make_surface(viewport, Rect2(Vector2.ZERO, Vector2(dimensions)), scale_factor)
				outputs.append({"viewport": viewport, "pitch": pitch, "background": background, "mode": mode})
		var viewport := output_viewport(dimensions, Color.TRANSPARENT)
		var drawing := Drawing.new()
		drawing.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		viewport.add_child(drawing)
		direct.append({"viewport": viewport, "pitch": pitch, "drawing": drawing})
	for direction in ["N", "E", "S", "W"]:
		for index in range(25):
			var offsets: Array = config.offsets[direction]
			var commands: Array[Dictionary] = []
			var atlas_region := Rect2((index % 24 % 6) * 384, (index % 24 / 6) * 704, 384, 704)
			# Integer row division matches the original6x4 atlas frame order.
			atlas_region.position.y = int((index % 24) / 6) * 704
			for point in offsets:
				commands.append({"texture": atlases[direction], "destination": Rect2(point[0], point[1], 384, 704), "region": atlas_region})
			current_pipeline.set_grid_origin(Vector2.ZERO)
			reference_pipeline.set_grid_origin(Vector2.ZERO)
			current_canvas.commands = commands
			current_canvas.queue_redraw()
			var path := str(config.nativeReferenceDirectory).path_join("native-%s-%02d.png" % [direction, index])
			var pixels := Image.load_from_file(path)
			var texture := ImageTexture.create_from_image(pixels)
			reference_canvas.commands = [{"texture": texture, "destination": Rect2(0, 0, 896, 1216), "region": Rect2(0, 0, 896, 1216)}]
			reference_canvas.queue_redraw()
			for entry in direct:
				var factor := float(entry.pitch) / 256.0
				var drawing: Drawing = entry.drawing
				drawing.commands = []
				for command in commands:
					drawing.commands.append({"texture": command.texture, "destination": Rect2(command.destination.position * factor, command.destination.size * factor), "region": command.region})
				drawing.queue_redraw()
			await process_frame
			await RenderingServer.frame_post_draw
			await process_frame
			await RenderingServer.frame_post_draw
			for entry in outputs:
				var name := "%s-%s-%02d-%d-%s.png" % [entry.mode, direction, index, entry.pitch, entry.background]
				assert(entry.viewport.get_texture().get_image().save_png(destination.path_join(name)) == OK)
				captures.append({"direction": direction, "index": index, "atlas_frame": index % 24, "phase": -7.0 * index / 24.0, "pitch": entry.pitch, "background": entry.background, "mode": entry.mode, "path": ProjectSettings.globalize_path(destination.path_join(name))})
			if index == 0:
				for entry in direct:
					assert(entry.viewport.get_texture().get_image().save_png(destination.path_join("old-individual-mips-%s-%d.png" % [direction, entry.pitch])) == OK)
			# Additional moving-camera common subpixel roots at four critical loop times.
			if index in [0, 12, 23, 24]:
				for shift in [Vector2(0.25, 0.75), Vector2(0.5, 0.5), Vector2(0.875, 0.125)]:
					current_pipeline.set_grid_origin(shift)
					reference_pipeline.set_grid_origin(shift)
					var moved: Array[Dictionary] = []
					for command in commands:
						moved.append({"texture": command.texture, "destination": Rect2(command.destination.position + shift, command.destination.size), "region": command.region})
					current_canvas.commands = moved
					current_canvas.queue_redraw()
					reference_canvas.commands = [{"texture": texture, "destination": Rect2(shift, Vector2(896, 1216)), "region": Rect2(0, 0, 896, 1216)}]
					reference_canvas.queue_redraw()
					await process_frame
					await RenderingServer.frame_post_draw
					await process_frame
					await RenderingServer.frame_post_draw
					for entry in outputs:
						if entry.background != "transparent": continue
						var name := "%s-%s-%02d-%d-shift-%d-%d.png" % [entry.mode, direction, index, entry.pitch, roundi(shift.x * 1000), roundi(shift.y * 1000)]
						assert(entry.viewport.get_texture().get_image().save_png(destination.path_join(name)) == OK)
						captures.append({"direction": direction, "index": index, "atlas_frame": index % 24, "phase": -7.0 * index / 24.0, "pitch": entry.pitch, "background": "transparent", "mode": entry.mode, "native_root_shift": [shift.x, shift.y], "path": ProjectSettings.globalize_path(destination.path_join(name))})
			print("CAPTURE ", direction, " ", index)
	var record := {"godot": Engine.get_version_info(), "renderer": ProjectSettings.get_setting("rendering/renderer/rendering_method"), "source": "Actual imported mipmapped source2 atlas regions → native nearest GPU composition → premultiplied2x GPU reduction chain → weighted area presentation. Reference uses the corresponding actual native Blender3-module capture in the same compositor.", "pipelineAllocation": current_pipeline.allocation_record(), "captures": captures}
	var file := FileAccess.open("res://render-record.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(record, "  "))
	quit()
