extends SceneTree
## Capture actual service frames and a production-asset registration sheet.

const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
const ArtBook = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")

class RegistrationSheet extends Node2D:
	var art
	var clips: Array
	var font: Font

	func _draw() -> void:
		draw_rect(Rect2(0, 0, 1280, (clips.size() + 1) * 142), Color("ffefcf"))
		draw_string(font, Vector2(24, 42), "Six distinct frames · feet on tile centers · native sprite sources", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color("253b3b"))
		for row in range(clips.size()):
			var clip := str(clips[row])
			var y := 100.0 + row * 142.0
			draw_string(font, Vector2(16, y + 40), clip, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color("253b3b"))
			for phase in range(6):
				var center := Vector2(300 + phase * 160, y + 100)
				draw_rect(Rect2(center - Vector2(55, 55), Vector2(110, 110)), Color("ad987b"), false, 1.0)
				var key := str(art.animations[clip].frames[phase])
				var texture: Texture2D = art.get_texture(key)
				draw_texture_rect(texture, art.fit(key, center, Vector2(98, 122)), false)
				draw_line(center - Vector2(7, 0), center + Vector2(7, 0), Color("168c97"), 2)
				draw_line(center - Vector2(0, 7), center + Vector2(0, 7), Color("168c97"), 2)
				draw_string(font, center + Vector2(-4, 29), str(phase + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color("253b3b"))

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("An animation capture output is required.")
		quit(1)
		return
	var app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	app.advance_time(8.0)
	for frame in range(120):
		app.advance_time(1.0 / 24.0)
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(destination.path_join("frame_%03d.png" % frame))
	var art = ArtBook.new()
	art.reload()
	var clips: Array = []
	for clip in art.animations:
		if not str(clip).begins_with("belt"):
			clips.append(clip)
	clips.sort()
	clips.append("belt_horizontal")
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1280, (clips.size() + 1) * 142)
	viewport.transparent_bg = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var sheet := RegistrationSheet.new()
	sheet.art = art
	sheet.clips = clips
	sheet.font = Typography.body()
	sheet.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	viewport.add_child(sheet)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(destination.path_join("six-frame-registration.png"))
	print("Captured 120 actual service frames and all six-frame foot registrations.")
	app.queue_free()
	viewport.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)
