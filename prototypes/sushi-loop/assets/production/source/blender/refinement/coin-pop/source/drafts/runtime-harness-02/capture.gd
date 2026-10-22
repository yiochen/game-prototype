extends "res://scripts/restaurant_view.gd"
var output := ""
var sample_time := 0.0
var receipts: Array = []
func _ready() -> void:
	native_composition_enabled = false
	clip_contents = false
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	font = ThemeDB.fallback_font
	heading = font
	art.objects = JSON.parse_string(FileAccess.get_file_as_string("res://objects.json"))
	art.cell_size = 128.0
	var args := OS.get_cmdline_user_args()
	output=args[1]
	for tick in range(36):
		sample_time=tick/30.0
		time=sample_time
		receipts.append({"tick":tick,"age":time,"visible":time<0.9,"alpha":1.0-time/0.9 if time<0.9 else 0.0,"actualArtBookFrame":art.frame_data("coin-pop","pop","S",time).frame,"basePolicy":"cell_base(pop.x,pop.y), no offset"})
		queue_redraw()
		await get_tree().process_frame
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(output.path_join("%03d.png" % tick))
	var f := FileAccess.open(output.path_join("runtime-receipts.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(receipts,"  "))
	print("COIN_RUNTIME_CAPTURE_COMPLETE "+str(receipts.size()))
	get_tree().quit(0)
func _process(_delta: float) -> void:
	pass
func _draw() -> void:
	if font == null: return
	draw_rect(Rect2(0,0,1080,760),Color("f8f1df"))
	caption("ACTUAL GODOT / inherited current sprite registration + verbatim sale loop",Vector2(16,28),19)
	caption("0.9s runtime fade / same customer ground root / age=%.3fs"%sample_time,Vector2(16,53),18)
	for row in range(2):
		cell=128.0 if row==0 else 64.0
		for col in range(3):
			var bg := [Color("f8f1df"),Color("78888b"),Color("182c3b")][col]
			var panel := Rect2(col*360,72+row*344,360,340)
			draw_rect(panel,bg)
			var ink := Color("ffffff") if col==2 else Color("253b3b")
			draw_string(font,Vector2(col*360+12,96+row*344),"cell%dpx / repeated registered instances"%int(cell),HORIZONTAL_ALIGNMENT_LEFT,-1,15,ink)
			var base := Vector2(col*360+98,380 if row==0 else 676)
			floor_origin=base-Vector2.ONE*cell*.5
			for x in [0.0,1.25]:
				var at:=cell_base(x,0)
				sprite("floor-cream",at,"static","S",0.0,cell)
				_seat_at({"facing":"south"},at,cell)
				_customer_at({"appearance":1,"phase":"waiting","visual_phase":"seated-wait","facing":"south","visual_elapsed":sample_time},at,cell)
			sale_pops=[{"x":0.0,"y":0.0,"time":0.0},{"x":1.25,"y":0.0,"time":0.0}]
			_actual_sale_loop()
func _actual_sale_loop() -> void:
	for pop in sale_pops:
		var age := time - float(pop.time)
		if age >= 0.0 and age < 0.9:
			# Native pop frames already rise above this registered customer root.
			# Keep its authored scale/motion and the existing quiet alpha fade.
			sprite("coin-pop", cell_base(float(pop.x), float(pop.y)), "pop", "S", 0.0 if reduced_motion else age, -1.0, Color(1, 1, 1, 1.0 - age / 0.9))

