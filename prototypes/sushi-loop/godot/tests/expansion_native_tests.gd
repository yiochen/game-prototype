extends SceneTree
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expansion_book.gd")
var app
var count := 0
var failures: Array[String] = []
var output := ""
func _init() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func frames() -> void:
	for i in range(3): await process_frame
func touch(at: Vector2, pressed: bool, canceled := false) -> void:
	var event := InputEventScreenTouch.new();event.index = 19;event.position = app.get_viewport_transform()*at;event.pressed = pressed;event.canceled = canceled
	Input.parse_input_event(event);await frames()
func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center();await touch(at,true);await touch(at,false)
func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func ink(identity: String) -> Vector2:
	for record in app.world.sprite_hits():
		if record.owner_id != identity: continue
		var visible: Rect2 = record.rect.intersection(app.world.hud_area())
		for y in range(ceili(visible.position.y)+2,floori(visible.end.y)-2,4):
			for x in range(ceili(visible.position.x)+2,floori(visible.end.x)-2,4):
				var at := Vector2(x,y)
				if app._floor_drop(at) and app.world.object_at(at).get("id","") == identity: return at
	return Vector2(-1,-1)
func covered() -> bool:
	return not app.session.snapshot().expansion.dock_open
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var requested := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if requested.size() == 2: root.size = Vector2i(int(requested[0]),int(requested[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate();app.show_editor_gallery = true;app.simulation_enabled = false;root.add_child(app);await frames()
	app.show_editor_gallery = false;app.show_gallery = false;app.world.show_gallery = false
	app.session = Session.new_session(19,{"starting_coins":10000});app.session.command({"type":"set_camera","x":4.0,"y":0.0});app._refresh();app._layout();await frames()
	check(app.session.snapshot().expansion.patches.size() == 41,"real renderer has 41 individual objects")
	check(not app.world.render_plan().any(func(p):return p.get("key","").begins_with("wall-")),"edge-to-edge room has no side wall")
	check(app.world.render_plan().filter(func(p):return p.get("owner_id","") == "armchair-west").size() == 1,"new approved model participates in renderer/picking")
	await capture("01-restaurant")
	var original: Dictionary = app.session.save_data()
	var point := ink("landmark-submarine")
	check(point.x >= 0,"covered submarine has visible painted hit pixels")
	if point.x >= 0: await touch(point,true);await touch(point,false)
	check(app.clearance_toast.visible and app.clearance_toast.text == "Clear all surrounding trash first.","covered-area touch shows cleanup toast without revealing its contents")
	check(app.session.save_data() == original,"toast changes no coins, camera or visits")
	await capture("02-submarine-blocked")
	point = ink("armchair-west")
	check(point.x >= 0,"small trash has a real sprite hit target")
	if point.x >= 0: await touch(point,true);await touch(point,false)
	check(app.clearance_ui.visible,"painted trash tap opens native confirmation")
	if not app.clearance_ui.visible: app._open_clearance("armchair-west")
	check(app.clearance_ui.title.text == "Clear this patch?" and app.clearance_ui.preview.entry.art_id == "garbage-armchair","minimal title and matching whole-object preview")
	check(app.session.save_data() == original,"inspection keeps camera and game state fixed")
	var physical: float = app.get_viewport_transform().get_scale().x
	for button in [app.clearance_ui.cancel,app.clearance_ui.clear_button]:
		check(button.size.x*physical >= 44 and button.size.y*physical >= 44,"44px native clearance action")
		check(not button.accessibility_name.is_empty(),"native action has an accessible name")
	check(app.clearance_ui.panel.get_global_rect().position.y >= app.world.hud_area().position.y and app.clearance_ui.panel.get_global_rect().end.y <= app.world.hud_area().end.y+.1,"popup fits phone/landscape")
	await capture("03-armchair-confirmation")
	await touch(app.world.hud_area().position+Vector2(4,4),true);await touch(app.world.hud_area().position+Vector2(4,4),false)
	check(app.clearance_ui.visible and app.session.save_data() == original,"outside taps keep the confirmation and state")
	await tap(app.clearance_ui.cancel);check(not app.clearance_ui.visible and app.session.save_data() == original,"Cancel keeps everything in place")
	app._open_clearance("armchair-west");app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames()
	check(not app.clearance_ui.visible and app.session.save_data() == original,"Android Back cancels without moving camera")
	app._open_clearance("armchair-west");await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),true);app.notification(Node.NOTIFICATION_APPLICATION_PAUSED);await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),false);app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);await frames()
	check(app.session.save_data() == original,"background/resume cancels a held Clear without payment")
	app.clearance_ui.dismiss()
	app._open_clearance("armchair-west");await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),true);await capture("04-clear-pressed");await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),false)
	await create_timer(.30).timeout;await frames()
	check(app.session.snapshot().coins == 9955 and app.session.snapshot().expansion.cleared == ["armchair-west"],"touch clear commits one real payment")
	check(app.session.snapshot().camera == original.state.camera,"successful clear never moves camera")
	check(covered(),"one neighbor cannot uncover the submarine")
	check(not app.world.sprite_hits().any(func(p):return p.owner_id == "armchair-west"),"cleared object disappears from rendering and picking")
	await capture("05-first-trash-cleared")
	var reloaded = Session.new_session(2)
	check(reloaded.restore(app.store.load_session()) and reloaded.snapshot().expansion.cleared == ["armchair-west"],"native clear is durable")
	# Complete all remaining side/corner neighbors through the production command path.
	for id in ["dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]:
		app._open_clearance(id);check(app.clearance_ui.visible,"next bordering trash is reachable")
		await tap(app.clearance_ui.clear_button);await create_timer(.28).timeout;await frames()
		check(app.session.snapshot().camera == original.state.camera,"every clearance preserves camera")
		check(covered(),"even the final surrounding clearance leaves the cover in place")
	check(app.session.snapshot().expansion.patches.size() == 34,"distant trash need not be removed")
	point = ink("landmark-submarine")
	if point.x >= 0: await touch(point,true);await touch(point,false)
	else: app._open_landmark("Submarine")
	check(app.clearance_ui.visible and app.clearance_ui.title.text == "reveal?" and not app.clearance_ui.well.visible,"cover tap opens an anonymous reveal confirmation")
	await tap(app.clearance_ui.clear_button)
	await create_timer(app.world.dock_reveal_duration()+app.world.COVER_FADE_SECONDS+.1).timeout;await frames()
	await capture("06-dock-revealed")
	check(app.clearance_ui.unlock_popup and app.clearance_ui.title.text == "Exhibition Unlocked","complete reveal shows the approved unlock popup")
	await tap(app.clearance_ui.clear_button);check(app.clearance_ui.visible and app.clearance_ui.title.text == "Submarine","Let's go opens the native submarine entry after full cleanup");await capture("07-submarine");app.clearance_ui.dismiss()
	app._open_landmark("Workshop");check(app.clearance_ui.visible and app.clearance_ui.title.text == "Workshop","Workshop shares the same prerequisite");app.clearance_ui.dismiss()
	app.session = Session.new_session(19,{"starting_coins":0});app._refresh();app._layout();app._open_clearance("dock-access");await frames()
	check(app.clearance_ui.clear_button.disabled and app.clearance_ui.price_label.text == "180" and not app.clearance_ui.cancel.disabled,"disabled Clear keeps its readable cost and Cancel")
	await capture("08-not-enough-coins");app.clearance_ui.dismiss()
	app.session = Session.new_session(19,{"starting_coins":10000});app._editor_command({"type":"set_mode","mode":"edit"});app._open_clearance("sofa-west");await frames()
	var editing: Dictionary = app.session.save_data();app.advance_time(30)
	check(app.session.save_data() == editing,"Edit remains paused during clearance")
	await capture("09-edit-clearance");app.clearance_ui.dismiss()
	app.clearance_ui.gallery = true;app._open_clearance("dock-access")
	for sample in ["normal","pressed","disabled","selected"]:
		app.clearance_ui.sample = sample;app.clearance_ui.refresh(app.session.snapshot());app.clearance_ui.layout(app.world.hud_area());await frames();await capture("10-gallery-"+sample)
	check(app.clearance_ui.get_script() == preload("res://scripts/clearance_presentation.gd"),"gameplay and Shared use the same component")
	app.clearance_ui.dismiss();app.clearance_ui.gallery = false;app.clearance_ui.sample = "normal"
	app.session = Session.new_session(19,{"starting_coins":10000});app._refresh();app._layout()
	for change in [Vector2(100000,100000),Vector2(-100000,-100000)]:
		app._pan(change)
		var room := Rect2(app.world.floor_origin-Vector2(float(app.session.snapshot().camera.x),float(app.session.snapshot().camera.y))*app.world.cell,Vector2(21,13)*app.world.cell)
		check(room.grow(.1).encloses(app.world.hud_area()),"pan bounds never reveal outside the restaurant")
	app.session.command({"type":"set_camera","x":4,"y":0});app._refresh()
	var original_store = app.store
	var obstacle := "user://clearance-write-obstacle-%s" % OS.get_process_id()
	var blocker := FileAccess.open(obstacle,FileAccess.WRITE);blocker.store_string("file blocks save directory");blocker.close()
	app.store = preload("res://scripts/save_store.gd").new(obstacle)
	app._open_clearance("armchair-west");await tap(app.clearance_ui.clear_button);await create_timer(.30).timeout;await frames()
	check(app.save_blocked and app.session.snapshot().coins == 9955,"save failure retains one accepted clearance and blocks further edits")
	await capture("11-save-retry")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle));app._retry_restore();await frames()
	check(not app.save_blocked and app.store.load_session().state.expansion.cleared == ["armchair-west"],"Retry durably writes the same clearance without replaying its debit")
	check(app.session.snapshot().coins == 9955,"Retry never charges again")
	app.store = original_store
	var report := {"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":count,"failures":failures}
	if not output.is_empty(): FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	app.audio.set_muted(true);app.audio._music.stop();app.queue_free();await frames();await create_timer(.1).timeout
	print("Expansion native: %s checks; %s failures" % [count,failures.size()]);quit(0 if failures.is_empty() else 1)
