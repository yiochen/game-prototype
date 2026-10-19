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
		draw_rect(Rect2(0, 0, 1728, 80 + clips.size() * 200), Color("ffefcf"))
		draw_string(font, Vector2(24, 42), "Approved native sprites · 12 fps · complete frames at one shared tile scale", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color("253b3b"))
		for row in range(clips.size()):
			var item: Array = clips[row]
			var y := 80.0 + row * 200.0
			draw_string(font, Vector2(16, y + 80), str(item[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color("253b3b"))
			draw_string(font, Vector2(16, y + 106), "%s · %s" % [item[1], item[2]], HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color("253b3b"))
			for column in range(12):
				var phase: int = column + int(item[3])
				var center := Vector2(285 + column * 120, y + 152)
				draw_rect(Rect2(center - Vector2(32, 32), Vector2(64, 64)), Color("ad987b"), false, 1.0)
				var texture: Texture2D = art.get_texture(str(item[0]), str(item[1]), str(item[2]), (float(phase) + 0.02) / 12.0)
				draw_texture_rect(texture, art.registered_rect(str(item[0]), center, 64.0, str(item[1]), str(item[2])), false)
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
	var clips: Array = [
		["chef-lena", "work", "N", 0],
		["chef-lena", "hold", "N", 0],
		["chef-lena", "load", "N", 0],
		["customer-rosa", "walk", "S", 0],
		["customer-rosa", "sit-down", "S", 0],
		["customer-rosa", "eat", "S", 0],
		["customer-rosa", "stand-up", "S", 0],
		["belt-straight-e", "running", "S", 0],
		["belt-straight-e", "running", "S", 12],
	]
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1728, 80 + clips.size() * 200)
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
	viewport.get_texture().get_image().save_png(destination.path_join("catalog-frame-registration.png"))
	print("Captured 120 actual service frames and complete 12/24-frame native registration rows.")
	app.queue_free()
	viewport.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)
