extends SceneTree
## Native unlock flow, exact approved illustration, shared controls and lifecycle.
const Session = preload("res://scripts/session.gd")
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
	var event := InputEventScreenTouch.new();event.index = 25;event.position = app.get_viewport_transform()*at;event.pressed = down
	Input.parse_input_event(event);await frames()
func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center();await touch(at,true);await touch(at,false)
func key(code: Key, shift := false) -> void:
	var event := InputEventKey.new();event.keycode = code;event.pressed = true;event.shift_pressed = shift;Input.parse_input_event(event);await frames()
	event = InputEventKey.new();event.keycode = code;event.pressed = false;Input.parse_input_event(event);await frames()
func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	check(root.get_texture().get_image().save_png(output.path_join(name+".png")) == OK,"GPU capture: "+name)
func cover_present() -> bool:
	return app.world.render_plan().any(func(p):return p.get("key") == "dock-cover")
func prepare() -> void:
	app.clearance_ui.dismiss();app.dock_unlock_pending = false
	app.session = Session.new_session(19,{"starting_coins":10000})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]: app.session.command({"type":"clear_trash","id":identity})
	app.session.command({"type":"set_mode","mode":"edit"});app.session.command({"type":"set_camera","x":4,"y":0})
	app.world.time = 0;app.world.dock_reveal_started = -1;app.world.reduced_motion = false;app._refresh();app._layout();await frames()
func reveal() -> void:
	app._open_landmark("Submarine");await tap(app.clearance_ui.clear_button)
	app.world.time = app.world.dock_reveal_started+1.19;app._refresh();await frames()

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var size := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if size.size() == 2: root.size = Vector2i(int(size[0]),int(size[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate();app.show_editor_gallery = true;app.simulation_enabled = false;root.add_child(app);await frames()
	app.show_editor_gallery = false;app.show_gallery = false;app.world.show_gallery = false;app.set_process(false)
	await prepare()
	var before: Dictionary = app.session.save_data()
	check(cover_present() and not app.dock_unlock_pending and not app.clearance_ui.unlock_popup,"ready surrounding trash never auto-reveals or shows the unlock popup")
	app._open_landmark("Submarine")
	check(app.clearance_ui.title.text == "reveal?" and not app.clearance_ui.unlock_art.visible and not app.clearance_ui.close_button.visible,"anonymous question retains its no-spoiler presentation")
	await tap(app.clearance_ui.cancel);check(app.session.save_data() == before and cover_present(),"Cancel does not unlock")
	app._open_landmark("Submarine");await tap(app.clearance_ui.clear_button)
	var accepted: Dictionary = app.session.save_data()
	check(app.clearance_ui.visible and app.clearance_ui.busy and not app.clearance_ui.panel.visible and app.dock_unlock_pending,"confirmed reveal keeps one full-screen input shield until the animation ends")
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await key(KEY_ESCAPE)
	check(app.dock_unlock_pending and app.clearance_ui.busy,"Back cannot cancel a committed reveal or skip its animation")
	app.world.time = app.world.dock_reveal_started+1.08;app._refresh();await frames()
	check(cover_present() and not app.clearance_ui.panel.visible,"unlock card waits through the complete frame fade")
	app.world.time += .12;app._refresh();await frames()
	var ui = app.clearance_ui
	check(not cover_present() and ui.visible and ui.unlock_popup and not ui.busy and not app.dock_unlock_pending,"unlock appears only after the whole cover/frame disappears")
	check(ui.title.text == "Exhibition Unlocked" and ui.panel.accessibility_name == "Exhibition Unlocked","exact requested heading and accessible dialog name")
	check(ui.clear_caption.text == "Let's go" and ui.clear_button.accessibility_name == "Let's go" and ui.close_button.accessibility_name == "Close","native primary and standard X labels")
	check(ui.unlock_art.visible and ui.unlock_art.texture.get_size() == Vector2(1536,1024),"the exact approved full-resolution underwater art is loaded")
	check(is_equal_approx(ui.unlock_art.size.x/ui.unlock_art.size.y,1.5),"illustration retains its full 3:2 aspect ratio")
	check(ui.unlock_art.material.shader.resource_path == "res://scripts/rounded_image.gdshader" and float(ui.unlock_art.material.get_shader_parameter("corner_radius")) > 0,"rounded clipping is separate from the illustration")
	check(not ui.cancel.visible and not ui.well.visible and not ui.preview.is_visible_in_tree() and not ui.price_label.visible and not ui.price_coin.visible,"unlock has no clearance preview, price, extra Cancel or currency")
	var physical: float = app.get_viewport_transform().get_scale().x
	var card: Rect2 = ui.panel.get_global_rect();var area: Rect2 = app.world.hud_area()
	check(area.encloses(card),"unlock card fits the visible phone or landscape area")
	for control in [ui.title,ui.unlock_art,ui.close_button,ui.clear_button]: check(card.encloses(control.get_global_rect()),"card contains "+str(control.name))
	for button in [ui.close_button,ui.clear_button]:
		check(button.size.x*physical >= 44 and button.size.y*physical >= 44,"44px minimum native touch target: "+button.accessibility_name)
	check(ui.title.get_global_rect().end.x <= ui.close_button.get_global_rect().position.x,"heading leaves a clear independent X target")
	check(get_root().gui_get_focus_owner() == ui.clear_button,"primary action owns opening keyboard focus")
	await key(KEY_TAB);check(root.gui_get_focus_owner() == ui.close_button,"Tab traps focus at the X")
	await key(KEY_TAB,true);check(root.gui_get_focus_owner() == ui.clear_button,"Shift-Tab returns to Let's go")
	await capture("01-unlocked")
	await touch(area.position+Vector2(3,3),true);await touch(area.position+Vector2(3,3),false)
	check(ui.unlock_popup and ui.visible and app.session.save_data() == accepted,"outside taps preserve the popup and saved room")
	await touch(ui.clear_button.get_global_rect().get_center(),true);await capture("02-go-pressed")
	app.notification(Node.NOTIFICATION_APPLICATION_PAUSED);await touch(ui.clear_button.get_global_rect().get_center(),false);app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);await frames()
	check(ui.unlock_popup and ui.visible and app.session.save_data() == accepted,"backgrounding cancels a held Let's go without navigation")
	await touch(ui.close_button.get_global_rect().get_center(),true);await capture("03-x-pressed")
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);await touch(ui.close_button.get_global_rect().get_center(),false)
	check(ui.unlock_popup and ui.visible,"focus loss cancels a held X")
	await tap(ui.close_button);check(not ui.visible and not cover_present() and app.session.save_data() == accepted,"normal X dismisses to the same saved uncovered room")
	await capture("04-dismissed")
	app._refresh();await frames();check(not ui.visible and not app.dock_unlock_pending,"dismissal does not replay the one-time unlock")
	var restored = Session.new_session(1);check(restored.restore(app.store.load_session()),"confirmed reveal reloads from disk")
	app.session = restored;app.world.dock_reveal_started = -1;app._refresh();await frames()
	check(not ui.visible and not cover_present(),"reloaded revealed saves have no cover and no replay popup")
	accepted = app.session.save_data() # Restore may normalize versioned snapshot caches.
	ui.open_unlock(app.session.snapshot());await key(KEY_ESCAPE);check(not ui.visible and app.session.save_data() == accepted,"Escape closes without mutating the accepted reveal")
	ui.open_unlock(app.session.snapshot());app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);check(not ui.visible and app.session.save_data() == accepted,"Android Back closes without leaving the restaurant")
	ui.open_unlock(app.session.snapshot());await tap(ui.clear_button)
	check(ui.visible and not ui.unlock_popup and ui.destination == "Submarine" and ui.title.text == "Submarine","Let's go uses the existing native Submarine entry")
	check(app.session.save_data() == accepted,"opening the entry never charges, moves the camera, or starts a journey")
	await capture("05-submarine-entry");ui.dismiss()
	await prepare();app.world.reduced_motion = true;app._open_landmark("Submarine");await tap(ui.clear_button)
	check(not cover_present() and not app.world.dock_revealing() and ui.unlock_popup and ui.visible,"reduced motion removes the cover immediately and still shows the unlock")
	await capture("06-reduced-motion");ui.dismiss();app.world.reduced_motion = false
	ui.gallery = true;ui.open_unlock(app.session.snapshot());ui.sample = "pressed";ui.layout(app.world.hud_area());await frames();await capture("07-gallery-pressed")
	check(ui.get_script() == preload("res://scripts/clearance_presentation.gd"),"gameplay and gallery share the exact native unlock component")
	ui.dismiss();ui.gallery = false;ui.sample = "normal"
	await prepare()
	var original_store = app.store;var obstacle := "user://unlock-write-obstacle-%s" % OS.get_process_id()
	var blocker := FileAccess.open(obstacle,FileAccess.WRITE);blocker.store_string("file blocks save directory");blocker.close()
	app.store = preload("res://scripts/save_store.gd").new(obstacle)
	app._open_landmark("Submarine");await tap(ui.clear_button)
	check(app.save_blocked and app.dock_unlock_pending and not ui.visible and app.recovery != null,"save failure yields the reveal shield to the existing Retry recovery")
	app.world.time = app.world.dock_reveal_started+1.2;app._refresh()
	check(not ui.visible and app.dock_unlock_pending,"unlock waits for the accepted reveal to be saved")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle));await tap(app.recovery_retry);await frames()
	check(not app.save_blocked and app.recovery == null and ui.unlock_popup and ui.visible,"a real native Retry tap saves the reveal then opens its one-time popup")
	check(app.store.load_session().state.expansion.revealed and app.session.snapshot().coins == 9180,"Retry saves the exact reveal with no extra charge")
	await capture("08-retry-unlocked");ui.dismiss();app.store = original_store
	var report := {"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":checks,"failures":failures}
	if not output.is_empty(): FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	app.audio.set_muted(true);app.audio._music.stop();app.queue_free();await frames()
	print("Exhibition unlock native: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
