extends SceneTree
## Actual cover layers, native one-shot playback and durable unlock boundary.
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
	var event := InputEventScreenTouch.new();event.index = 21;event.position = app.get_viewport_transform()*at;event.pressed = down
	Input.parse_input_event(event);await frames()

func tap(button: Control) -> void:
	var at := button.get_global_rect().get_center();await touch(at,true);await touch(at,false)

func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	check(root.get_texture().get_image().save_png(output.path_join(name+".png")) == OK,"native cover capture: "+name)

func item(key: String) -> Dictionary:
	for entry in app.world.render_plan():
		if entry.get("key") == key: return entry
	return {}

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var size := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if size.size() == 2: root.size = Vector2i(int(size[0]),int(size[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate();app.show_editor_gallery = true;app.simulation_enabled = false;root.add_child(app);await frames()
	app.show_editor_gallery = false;app.show_gallery = false;app.world.show_gallery = false
	app.set_process(false) # Only presentation time advances explicitly below.
	app.session = Session.new_session(19,{"starting_coins":10000})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8"]:
		check(app.session.command({"type":"clear_trash","id":identity}).get("changed",false),"border fixture clears "+identity)
	app.session.command({"type":"set_mode","mode":"edit"})
	app.session.command({"type":"set_camera","x":4,"y":0})
	app.world.time = 0;app.world.dock_reveal_started = -1
	app._refresh();app._layout();await frames()
	check(not app.session.snapshot().expansion.dock_open,"the last diagonal object still prevents access")
	var plan: Array = app.world.render_plan()
	for key in ["dock-floor","submarine-yellow","workshop-hut","dock-cover"]:
		check(plan.filter(func(p):return p.get("key") == key).size() == 1,"permanent layer exists while covered: "+key)
	check(plan.find(item("dock-floor")) < plan.find(item("submarine-yellow")) and plan.find(item("dock-floor")) < plan.find(item("workshop-hut")),"deck is behind both objects")
	check(plan.find(item("dock-cover")) > plan.find(item("submarine-yellow")) and plan.find(item("dock-cover")) > plan.find(item("workshop-hut")),"cloth covers the existing submarine and hut")
	check(item("dock-cover").clip == "static","closed dock uses its registered covered pose")
	var root_before: Vector2 = item("dock-cover").base
	var bounds: Rect2 = app.world.art.registered_rect("dock-cover",root_before,app.world.cell)
	var before: Dictionary = app.session.save_data()
	app._open_landmark("Workshop")
	check(app.clearance_toast.visible and not app.clearance_ui.visible and app.session.save_data() == before,"visible objects through cloth gaps remain gated")
	await capture("01-covered-layers")
	app._open_clearance("trash-10-9");app._confirm_clearance("trash-10-9")
	check(app.session.snapshot().expansion.dock_ready and not app.session.snapshot().expansion.dock_open and not app.world.dock_revealing(),"last surrounding clearance only makes the cover ready")
	await create_timer(.30).timeout;await frames()
	app.world.time += .30;app._refresh();await frames()
	check(item("dock-cover").clip == "static" and item("dock-cover").get("tint",Color.WHITE) == Color.WHITE,"ready cover stays closed and returns to its normal brightness")
	var pending: Dictionary = app.session.save_data()
	app._open_landmark("Submarine")
	check(app.clearance_ui.visible and app.clearance_ui.title.text == "reveal?","cover tap opens the requested anonymous question")
	check(not app.clearance_ui.well.visible and not app.clearance_ui.price_coin.visible and not app.clearance_ui.price_label.visible,"reveal question shows neither contents nor a price")
	check(app.clearance_ui.clear_caption.text == "Reveal" and app.clearance_ui.clear_button.accessibility_name == "Reveal" and app.clearance_ui.cancel.text == "Cancel","minimal native Cancel and Reveal actions")
	check(app.clearance_ui.panel.get_global_rect().position.y >= app.world.hud_area().position.y and app.clearance_ui.panel.get_global_rect().end.y <= app.world.hud_area().end.y+.1,"compact confirmation fits the visible phone/landscape area")
	var physical: float = app.get_viewport_transform().get_scale().x
	for button in [app.clearance_ui.cancel,app.clearance_ui.clear_button]: check(button.size.x*physical >= 44 and button.size.y*physical >= 44,"reveal action retains its 44px touch target")
	await capture("02-reveal-question")
	await touch(app.world.hud_area().position+Vector2(3,3),true);await touch(app.world.hud_area().position+Vector2(3,3),false)
	check(app.clearance_ui.visible and app.session.save_data() == pending,"outside taps retain the question and never reveal")
	await tap(app.clearance_ui.cancel)
	check(not app.clearance_ui.visible and app.session.save_data() == pending,"Cancel keeps the cover and saved restaurant unchanged")
	app._open_landmark("Workshop");app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames()
	check(not app.clearance_ui.visible and app.session.save_data() == pending,"Back cancels the same anonymous question from either target")
	app._open_landmark("Submarine");await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),true)
	app.notification(Node.NOTIFICATION_APPLICATION_PAUSED);await touch(app.clearance_ui.clear_button.get_global_rect().get_center(),false);app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);await frames()
	check(app.session.save_data() == pending,"backgrounding cancels a held Reveal without uncovering")
	await tap(app.clearance_ui.clear_button);await frames()
	check(app.session.snapshot().expansion.dock_open and app.world.dock_revealing(),"only a confirmed Reveal starts the opening")
	check(is_equal_approx(app.world.dock_reveal_started,app.world.time),"confirmed reveal starts without a second trash-removal delay")
	check(app.session.snapshot().coins == 9180 and app.session.snapshot().camera == before.state.camera,"reveal adds no charge and never moves the camera")
	var accepted: Dictionary = app.session.save_data()
	check(not accepted.state.has("dock_reveal_started"),"animation is transient and never enters the save")
	app._open_landmark("Submarine")
	check(app.clearance_ui.visible and app.clearance_ui.busy and not app.clearance_ui.panel.visible,"full-scene input shield prevents destinations from interrupting the rolling cloth")
	var clip: Dictionary = app.world.art.clip_data("dock-cover","uncover")
	check(clip.frames == 12 and clip.fps == 12 and not clip.loop,"reuses all twelve native one-shot frames at their original timing")
	for index in range(12):
		app.world.time = app.world.dock_reveal_started+float(index)/12.0+.001
		app._refresh();await frames()
		var cover := item("dock-cover")
		var frame: Dictionary = app.world.art.frame_data("dock-cover",cover.clip,"S",cover.seconds)
		check(cover.clip == "uncover" and frame.frame == index,"native cover frame advances in order: %s" % index)
		check(cover.base.is_equal_approx(root_before) and app.world.art.registered_rect("dock-cover",cover.base,app.world.cell,cover.clip).is_equal_approx(bounds),"native root and whole-frame scale stay fixed: %s" % index)
		await capture("roll-%02d" % index)
	app.world.time = app.world.dock_reveal_started+app.world.dock_reveal_duration()+.09
	app._refresh();await frames()
	check(app.world.dock_revealing() and item("dock-cover").tint.a > 0 and item("dock-cover").tint.a < 1,"the complete cover fades out after its native roll-up")
	await capture("cover-fading")
	app.world.time += .10;app._refresh();await frames()
	check(not app.world.dock_revealing() and item("dock-cover").is_empty(),"cloth, posts and frame are removed after opening")
	check(app.session.save_data() == accepted,"presentation in Edit changes no visits, clocks, coins, layout or RNG")
	await capture("03-cover-removed")
	check(app.clearance_ui.visible and app.clearance_ui.unlock_popup and app.clearance_ui.title.text == "Exhibition Unlocked","removed cover presents the approved unlock popup")
	await tap(app.clearance_ui.close_button)
	app._open_landmark("Submarine")
	check(app.clearance_ui.visible and app.clearance_ui.title.text == "Submarine","submarine opens after the cover finishes")
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	app._open_landmark("Workshop")
	check(app.clearance_ui.visible and app.clearance_ui.title.text == "Workshop","hut opens after the cover finishes")
	app.clearance_ui.dismiss()
	var restored = Session.new_session(1)
	check(restored.restore(app.store.load_session()),"unlock is durable independently of animation playback")
	app.session = restored;app.world.dock_reveal_started = -1;app.world.time = 0;app._refresh();await frames()
	check(item("dock-cover").is_empty() and not app.world.dock_revealing(),"reopening a confirmed reveal never restores the cover or replays opening")
	check(app.session.snapshot().coins == 9180 and app.session.snapshot().camera == before.state.camera,"reopening never charges or centers the view")
	app.world.dock_reveal_started = 0;app.world.reduced_motion = true;app._refresh();await frames()
	check(not app.world.dock_revealing() and item("dock-cover").is_empty(),"reduced motion immediately removes the revealed cover")
	await capture("04-reduced-motion")
	app.world.reduced_motion = false;app.world.dock_reveal_started = -1
	app.session = Session.new_session(19,{"starting_coins":10000})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]: app.session.command({"type":"clear_trash","id":identity})
	app._refresh();app._layout()
	var store = app.store;var obstacle := "user://reveal-write-obstacle-%s" % OS.get_process_id()
	var blocker := FileAccess.open(obstacle,FileAccess.WRITE);blocker.store_string("file blocks save directory");blocker.close()
	app.store = preload("res://scripts/save_store.gd").new(obstacle)
	app._open_landmark("Submarine");await tap(app.clearance_ui.clear_button);await frames()
	check(app.save_blocked and app.session.snapshot().expansion.dock_open,"save failure retains the accepted reveal behind Retry")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle));app._retry_restore();await frames()
	check(not app.save_blocked and app.store.load_session().state.expansion.revealed and app.session.snapshot().coins == 9180,"Retry saves exactly the accepted reveal without a new debit")
	app.store = store
	var report := {"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":checks,"failures":failures}
	if not output.is_empty(): FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	app.audio.set_muted(true);app.audio._music.stop();app.queue_free();await frames()
	print("Dock reveal native: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
