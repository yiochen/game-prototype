extends "res://scripts/restaurant_view.gd"
## Actual Godot rendering harness: inherited current renderer/feedback methods.
## Salmon/cucumber call customer_feedback; eel explicitly catalog-only.
var posed := false
var output := ""

func _ready() -> void:
	native_composition_enabled = false
	clip_contents = false
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	font = ThemeDB.fallback_font
	heading = font
	art.objects = JSON.parse_string(FileAccess.get_file_as_string("res://objects.json"))
	art.cell_size = 128.0
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--posed": posed = true
		if args[i] == "--output" and i + 1 < args.size(): output = args[i + 1]
	queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var error := image.save_png(output)
	print(JSON.stringify({"native_capture": output.get_file(), "error": error, "size": [image.get_width(), image.get_height()], "attachment": [0, -172], "posed": posed, "renderer": "Original RestaurantView.sprite/_customer_at/_feedback_at + ArtBook.frame_data/registered_rect", "eel": "Catalog-only direct sprite; not selected by customer_feedback"}))
	get_tree().quit(error)

func _process(_delta: float) -> void:
	pass

func _draw() -> void:
	if font == null: return
	draw_rect(Rect2(0, 0, 1080, 760), Color("f6f1e5"))
	caption("ACTUAL GODOT HARNESS / copied current native2D renderer methods", Vector2(20, 32), 20)
	caption("Full registered frames; current attachment(0,-172); separate native timer; no production-game screenshot claim", Vector2(20, 59), 15)
	caption("Pose offset(.06,-.02) cell applied equally to customer + feedback" if posed else "Unposed customer / original current attachment + timer", Vector2(20, 84), 16)
	var recipes := ["salmon_nigiri", "cucumber_maki", "eel_nigiri"]
	for index in range(3):
		var base := Vector2(180 + index * 350, 650)
		var guest := {"appearance": 0, "phase": "waiting", "visual_phase": "seated-wait", "visual_elapsed": 0.0, "facing": "south", "preference_phase": "active", "preferred_recipe_id": recipes[index], "preference_phase_elapsed": 1.0, "preference_progress": 0.6, "render_offset_x": 0.06 if posed else 0.0, "render_offset_y": -0.02 if posed else 0.0}
		sprite("stool-wood", base, "static", "S", 0, 128)
		_customer_at(guest, base, 128)
		if index < 2:
			_feedback_at(guest, base, 128)
		else:
			var bubble_base: Vector2 = base + customer_pose_offset(guest, 128) + BUBBLE_ATTACHMENT
			sprite("bubble-preference", bubble_base, "eel-idle", "S", 0, 128)
		caption(["Salmon / actual customer_feedback", "Cucumber / actual customer_feedback", "Eel / preserved catalog-only sprite"][index], Vector2(25 + index * 350, 710), 16)
		caption("82 logical balloon / 40 logical food", Vector2(25 + index * 350, 735), 15)
