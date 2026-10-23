extends "res://scripts/restaurant_view.gd"
## Isolated renderer harness. Current RestaurantView methods are inherited unchanged.
## Fixtures exercise existing feedback selection; no navigation simulation is claimed.
var output := ""
var sample_time := 1.0
var posed := false
var legacy := false
var runtime_sequence := false
var capture_reduced := false
var selections: Array = []

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
	# Real original selection tests, including exclusion of non-wander/non-admitted fixtures.
	for phase in ["walking", "leaving"]:
		for t in [0.0, 0.5, 11.0/12.0, 1.0, 1.5, 3.9]:
			var result := customer_feedback({"phase":phase,"navigation_mode":"wander","wander_elapsed":t})
			assert(result.object == "bubble-panic" and float(result.timer) == -1.0)
			assert(result.clip == ("idle" if reduced_motion or t >= 1.0 else "appear"))
			var actual := art.frame_data(result.object,result.clip,"S",float(result.seconds))
			assert(not actual.is_empty())
			selections.append({"phase":phase,"wander_elapsed":t,"feedback":result,"artBookFrame":actual.frame})
	assert(customer_feedback({"phase":"walking","navigation_mode":"goal"}).is_empty())
	assert(customer_feedback({"phase":"waiting","navigation_mode":"wander"}).is_empty())
	if runtime_sequence:
		for tick in range(48):
			sample_time = tick / 12.0
			await save_frame(output.path_join("runtime-%04d.png" % tick))
	else:
		await save_frame(output)
	print(JSON.stringify({"native_capture":output,"sequence_frames":48 if runtime_sequence else 1,"fps":12,"size":[1080,760],"attachment":[0,-90] if legacy else [0,-172],"posed":posed,"reduced_motion":reduced_motion,"selections":selections,"scope":"Actual current renderer methods with fixture dictionaries; no full game/navigation/save/UI test claim"}))
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
	draw_rect(Rect2(0,0,1080,760),Color("f6f1e5"))
	caption("ACTUAL GODOT isolated native2D consumer / copied current renderer",Vector2(20,32),20)
	caption("Full registered frame/root; exact candidate atlas; fixture state, no game simulation claim",Vector2(20,59),16)
	caption("LEGACY CATALOG ONLY: seated-wait/stool; attachment(0,-90)" if legacy else "CURRENT wander / walking+leaving / attachment(0,-172) / t=%.3fs" % sample_time,Vector2(20,86),17)
	caption("Shared customer+feedback pose offset(.06,-.02)cell" if posed else "Zero customer pose offset",Vector2(20,111),16)
	caption("Reduced motion: idle frame0" if reduced_motion else "Appear before1s, then looping idle; timer=-1, no timer ring or runtime fade",Vector2(20,135),16)
	for index in range(3):
		var pitch: float = [128.0,80.0,50.0][index]
		var base := Vector2(210+index*340,655)
		var phase := "leaving" if index == 1 else "walking"
		var guest := {"appearance":0,"phase":phase,"visual_phase":"walk","visual_elapsed":sample_time,"facing":"south","navigation_mode":"wander","wander_elapsed":sample_time,"render_offset_x":0.06 if posed else 0.0,"render_offset_y":-0.02 if posed else 0.0}
		if legacy:
			sprite("stool-wood",base,"static","S",0.0,pitch)
			sprite("customer-rosa",base,"seated-wait","S",sample_time,pitch)
			sprite("bubble-panic",base+Vector2(0,-90)*pitch/128.0,"idle","S",sample_time,pitch)
		else:
			_customer_at(guest,base,pitch)
			_feedback_at(guest,base,pitch)
		caption("Cell%.0fpx / balloon%.1fpx" % [pitch,82*pitch/128.0],Vector2(60+index*340,705),17)
		caption("Legacy catalog" if legacy else phase+" wander / current methods",Vector2(60+index*340,732),16)
