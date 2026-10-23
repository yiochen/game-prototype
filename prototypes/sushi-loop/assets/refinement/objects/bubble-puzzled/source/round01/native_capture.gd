extends "res://scripts/restaurant_view.gd"
## Isolated native2D consumer. Inherits exact current runtime methods unchanged.
var output := ""
var sample_time := 1.0
var posed := false
var legacy := false
var runtime_sequence := false
var capture_reduced := false

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
		if args[i] == "--output" and i + 1 < args.size(): output = args[i + 1]
		if args[i] == "--posed": posed = true
		if args[i] == "--legacy": legacy = true
		if args[i] == "--sequence": runtime_sequence = true
		if args[i] == "--reduced": capture_reduced = true
	reduced_motion = capture_reduced
	if runtime_sequence:
		for tick in range(48):
			sample_time = tick / 12.0
			await save_frame(output.path_join("runtime-%04d.png" % tick))
	else:
		await save_frame(output)
	print(JSON.stringify({"native_capture": output, "sequence_frames": 48 if runtime_sequence else 1, "fps": 12, "size": [1080,760], "attachment": [0,-90] if legacy else [0,-172], "posed": posed, "reduced_motion": reduced_motion, "methods": "Original RestaurantView._customer_at/_feedback_at/sprite/customer_feedback/customer_pose_offset and ArtBook.frame_data/registered_rect"}))
	get_tree().quit(0)

func save_frame(path: String) -> void:
	queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var error := image.save_png(path)
	if error != OK:
		push_error("Capture failed " + str(error))
		get_tree().quit(error)

func _process(_delta: float) -> void:
	pass

func _draw() -> void:
	if font == null: return
	draw_rect(Rect2(0,0,1080,760), Color("f6f1e5"))
	caption("ACTUAL GODOT isolated native2D consumer / copied current renderer", Vector2(20,32),20)
	caption("Full registered frame/root; exact candidate atlas; no production-game screenshot claim",Vector2(20,59),16)
	caption("LEGACY CATALOG ONLY: seated-wait/stool; attachment(0,-90)" if legacy else "CURRENT entrance_wait / standing / attachment(0,-172) / t=%.3fs" % sample_time,Vector2(20,86),17)
	caption("Shared customer+feedback pose offset(.06,-.02)cell" if posed else "Zero customer pose offset", Vector2(20,111),16)
	if reduced_motion: caption("Reduced motion: original customer_feedback uses idle frame0",Vector2(20,135),16)
	for index in range(3):
		var pitch: float = [128.0,80.0,50.0][index]
		var base := Vector2(210+index*340,655)
		var guest := {"appearance":0,"phase":"entrance_wait","visual_phase":"stand","visual_elapsed":sample_time,"facing":"south","entrance_wait_elapsed":sample_time,"entrance_wait_total":4.0,"render_offset_x":0.06 if posed else 0.0,"render_offset_y":-0.02 if posed else 0.0}
		if legacy:
			sprite("stool-wood",base,"static","S",0.0,pitch)
			sprite("customer-rosa",base,"seated-wait","S",sample_time,pitch)
			sprite("bubble-puzzled",base+Vector2(0,-90)*pitch/128.0,"idle","S",sample_time,pitch)
		else:
			_customer_at(guest,base,pitch)
			_feedback_at(guest,base,pitch)
		caption("Cell%.0fpx / balloon%.1fpx" % [pitch,82*pitch/128.0],Vector2(60+index*340,705),17)
		caption("Legacy catalog" if legacy else "Current Godot methods",Vector2(60+index*340,732),16)
