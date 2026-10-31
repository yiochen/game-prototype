extends SceneTree
## Sprite-only reachability shade and informative, non-spoiling blocked taps.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expansion_book.gd")
var app
var output := ""
var checks := 0
var failures: Array[String] = []

func _init() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message);printerr("FAIL: "+message)

func frames() -> void:
	for i in range(3): await process_frame

func touch(at: Vector2, down: bool) -> void:
	var event := InputEventScreenTouch.new();event.index = 20;event.position = app.get_viewport_transform()*at;event.pressed = down
	Input.parse_input_event(event);await frames()

func tap_at(at: Vector2) -> void:
	await touch(at,true);await touch(at,false)

func item(identity: String) -> Dictionary:
	for entry in app.world.render_plan():
		if entry.get("owner_id") == identity: return entry
	return {}

func ink(identity: String) -> Vector2:
	for record in app.world.sprite_hits():
		if record.owner_id != identity: continue
		var pixels: Image = record.texture.get_image()
		if pixels.is_compressed(): pixels.decompress()
		var bounds: Rect2 = record.rect.intersection(app.world.hud_area())
		for y in range(ceili(bounds.position.y)+3,floori(bounds.end.y)-3,4):
			for x in range(ceili(bounds.position.x)+3,floori(bounds.end.x)-3,4):
				var point := Vector2(x,y)
				if not app._floor_drop(point) or app.world.object_at(point).get("id","") != identity: continue
				var uv: Vector2 = (point-record.rect.position)/record.rect.size
				if pixels.get_pixelv(Vector2i(record.region.position+uv*record.region.size)).a >= .99: return point
	return Vector2(-1,-1)

func picture(name: String) -> Image:
	await frames()
	if DisplayServer.get_name() == "headless": return null
	await RenderingServer.frame_post_draw
	var image: Image = root.get_texture().get_image()
	if not output.is_empty(): check(image.save_png(output.path_join(name+".png")) == OK,"native capture: "+name)
	return image

func pixel(image: Image, at: Vector2) -> Color:
	return image.get_pixelv(Vector2i(app.get_viewport_transform()*at))

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var requested := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if requested.size() == 2: root.size = Vector2i(int(requested[0]),int(requested[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate();app.show_editor_gallery = true;app.simulation_enabled = false;root.add_child(app);await frames()
	app.show_editor_gallery = false;app.show_gallery = false;app.world.show_gallery = false;app.set_process(false)
	app.session = Session.new_session(19,{"starting_coins":10000});app.session.command({"type":"set_camera","x":4,"y":0});app._refresh();app._layout();await frames()
	check(item("sofa-west").get("tint",Color.WHITE) == Color.WHITE,"reachable trash keeps its original brightness")
	var locked: Color = item("cabinet-west").get("tint",Color.WHITE)
	check(locked.r < .7 and locked.r == locked.g and locked.g == locked.b and locked.a == 1,"unreachable sprite gets a neutral shade with unchanged alpha")
	var cover: Dictionary = app.world.render_plan().filter(func(p):return p.get("key") == "dock-cover")[0]
	check(cover.tint == locked,"unrevealable cover shares the same sprite-only shade")
	for key in ["dock-floor","submarine-yellow","workshop-hut"]:
		check(app.world.render_plan().filter(func(p):return p.get("key") == key)[0].get("tint",Color.WHITE) == Color.WHITE,"shade does not spread to the underlying "+key)
	check(app.clearance_targets.has("cabinet-west"),"blocked trash has a native keyboard target")
	check(app.clearance_targets["landmark-submarine"].accessibility_name == "Inspect cover","cover accessible name keeps the destination a surprise")
	var before: Dictionary = app.session.save_data()
	var point := ink("cabinet-west")
	check(point.x >= 0,"shaded object retains its opaque sprite hit pixels")
	var shaded := await picture("01-shaded-frontier")
	if point.x >= 0: await tap_at(point)
	check(app.clearance_toast.visible and app.clearance_toast.text == "Clear trash beside the open floor first." and not app.clearance_ui.visible,"blocked sprite touch explains clearance order")
	check(app.session.save_data() == before,"blocked touch changes no coins, camera, objects, visits or RNG")
	await picture("02-blocked-trash-hint")
	app.clearance_toast_seconds = .1
	if point.x >= 0: await tap_at(point)
	check(is_equal_approx(app.clearance_toast_seconds,3.2),"repeated blocked tap refreshes the toast")
	app.clearance_toast.hide()
	# A render-only control proves the actual GPU tint affects the sprite and
	# leaves surrounding pixels alone. The authoritative session is untouched.
	for patch in app.world.state.expansion.patches:
		if patch.id == "cabinet-west": patch.available = true
	app.world.queue_redraw()
	var unshaded := await picture("check-bright-sprite")
	if shaded != null and unshaded != null and point.x >= 0:
		check(pixel(shaded,point).get_luminance() < pixel(unshaded,point).get_luminance()*.85,"native GPU shade visibly darkens the painted sprite")
		var floor_point: Vector2 = app.world.cell_base(6,4)
		check(pixel(shaded,floor_point).is_equal_approx(pixel(unshaded,floor_point)),"native GPU shade does not cover surrounding floor")
	app._refresh()
	point = ink("landmark-submarine")
	if point.x >= 0: await tap_at(point)
	else: app._open_landmark("Submarine")
	check(app.clearance_toast.text == "Clear all surrounding trash first." and not "submarine" in app.clearance_toast.text.to_lower(),"cover hint never names the hidden destination")
	check(app.session.save_data() == before,"covered-area hint preserves the complete restaurant")
	await picture("03-covered-area-hint")
	# Compare the same unobstructed future-floor pixels under locked and fully
	# cleared masks. This catches tinting the tile instead of only its sprite.
	app.clearance_toast.hide();app.world.state.objects = [];app.world.state.customers = [];app.world.state.expansion.patches = []
	app.world.state.camera.y = maxf(0,13-app.world.hud_area().size.y/app.world.cell)
	app.world.queue_redraw();var locked_floor := await picture("check-locked-floor")
	app.world.state.expansion.cleared = Book.definition().patches.map(func(p):return p.id)
	app.world.queue_redraw();var clear_floor := await picture("check-cleared-floor")
	if locked_floor != null and clear_floor != null:
		check(pixel(locked_floor,app.world.cell_base(9,11)).is_equal_approx(pixel(clear_floor,app.world.cell_base(9,11))),"locked floor tiles retain exactly the same native pixels as cleared floor")
	app._refresh()
	app._open_clearance("sofa-west");app._confirm_clearance("sofa-west");await create_timer(.30).timeout;await frames()
	app.world.time += .30;app._refresh();await frames()
	check(item("cabinet-west").get("tint",Color.WHITE) == Color.WHITE,"clearing a neighbor immediately removes the next sprite's shade")
	check(app.session.snapshot().camera == before.state.camera,"clearance and shade updates leave camera fixed")
	await picture("04-next-trash-reachable")
	point = ink("cabinet-west")
	if point.x >= 0: await tap_at(point)
	else: app._open_clearance("cabinet-west")
	check(app.clearance_ui.visible and app.clearance_ui.patch.id == "cabinet-west","newly reachable pile opens normal priced confirmation")
	app.clearance_ui.dismiss()
	app.session.command({"type":"set_mode","mode":"edit"});app._refresh();before = app.session.save_data()
	app._open_clearance("trash-18-3")
	check(app.clearance_toast.visible and not app.clearance_ui.visible and app.session.save_data() == before,"Edit has the same blocked feedback without unpausing")
	await picture("05-edit-blocked")
	app.session = Session.new_session(19,{"starting_coins":0});app._refresh();app._layout()
	check(item("sofa-west").get("tint",Color.WHITE) == Color.WHITE,"insufficient coins do not change the reachability shade")
	app._open_clearance("sofa-west")
	check(app.clearance_ui.visible and app.clearance_ui.clear_button.disabled,"reachable unaffordable trash still explains its price in the existing dialog")
	app.clearance_ui.dismiss()
	app.session = Session.new_session(19,{"starting_coins":10000})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]:
		app.session.command({"type":"clear_trash","id":identity})
	app._refresh()
	cover = app.world.render_plan().filter(func(p):return p.get("key") == "dock-cover")[0]
	check(cover.clip == "static" and cover.get("tint",Color.WHITE) == Color.WHITE,"ready cover brightens but remains closed until confirmation")
	var report := {"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":checks,"failures":failures}
	if not output.is_empty(): FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	app.audio.set_muted(true);app.audio._music.stop();app.queue_free();await frames()
	print("Clearance feedback native: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
