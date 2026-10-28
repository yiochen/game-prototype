extends SceneTree
const Session = preload("res://scripts/session.gd")
var app
var count := 0
var failures: Array[String] = []
var output := ""
func _initialize() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func frames() -> void:
	for i in range(3): await process_frame
func touch(at: Vector2, pressed: bool, canceled := false) -> void:
	var event := InputEventScreenTouch.new();event.index = 18;event.position = app.get_viewport_transform()*at;event.pressed = pressed;event.canceled = canceled
	Input.parse_input_event(event);await frames()
func tap(control: Control) -> void:
	var point := control.get_global_rect().get_center();await touch(point,true);await touch(point,false)
func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func data_item(id: String) -> Dictionary:
	return app.session.snapshot().inventory.filter(func(entry):return entry.id==id)[0]
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size()==2: root.size = Vector2i(int(dimensions[0]),int(dimensions[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate();app.show_editor_gallery = true;app.simulation_enabled = false;root.add_child(app);await frames()
	app.show_editor_gallery = false;app.show_gallery = false;app.world.show_gallery = false
	app.session = Session.new_session(18,{"starting_coins":1240});app._refresh();app._layout();await frames()
	check(not app.shop.is_visible_in_tree() and not app.editor_ui.shop.is_visible_in_tree(),"Live has no Shop shortcut")
	check(not app._open_shop().ok,"Shop cannot open from Live")
	app._editor_command({"type":"set_mode","mode":"edit"});app._editor_command({"type":"editor_layer","layer":"layout"});await frames()
	check(app.editor_ui.shop.is_visible_in_tree(),"only the Edit tray has Shop")
	app.session.command({"type":"set_camera","x":.7,"y":.25});app.editor_ui.scroll_by(25*app.editor_ui.unit);app.editor_ui.commit_scroll();app._refresh();await frames()
	var original: Dictionary = app.session.save_data();var scroll: float = app.editor_ui.scroll_offsets.layout
	app.editor_ui.shop.grab_focus();await tap(app.editor_ui.shop);await frames()
	var shop = app.shop_ui
	check(shop.visible and not app.editor_ui.is_visible_in_tree(),"Shop hides the whole inventory tray")
	check(app.session.save_data()==original,"opening Shop preserves camera, coins, tray and clocks")
	check(app.advance_time(30).is_empty() and app.session.save_data()==original,"Shop keeps Edit paused")
	check(shop.rows.size()==5 and shop.rows.belt.stock.text=="Always available","single mixed catalog includes unlimited goods")
	var physical: float = app.get_viewport_transform().get_scale().x
	for id in shop.rows:
		var button: Button = shop.rows[id].buy
		check(button.size.x*physical>=44 and button.size.y*physical>=44,"cost touch target "+id)
		check(button.accessibility_name.begins_with("Buy ") and button.text==str(int(shop.rows[id].offer.cost)),"cost-only action retains accessible Buy "+id)
	for button in [shop.close_button,shop.bag_button]: check(button.size.x*physical>=44 and button.size.y*physical>=44,"close and bag targets >=44px")
	check(shop.panel.get_global_rect().position.x>=0 and shop.panel.get_global_rect().end.x<=app.size.x+.1,"portrait-contained popup")
	check(app.size.x>app.size.y or shop.panel.size.x>=app.world.portrait.size.x*.8,"phone popup uses portrait width at high pixel density")
	check(shop.catalog_backing.get_global_rect().end.y<=shop.bag_button.get_global_rect().position.y,"bag cannot cover catalog costs")
	await capture("01-shop")
	var initial_stock: int = data_item("belt-tile").count
	var point: Vector2 = shop.rows.belt.buy.get_global_rect().get_center()
	await touch(point,true);await capture("02-buy-pressed");await touch(point,false)
	check(app.session.snapshot().coins==1200 and data_item("belt-tile").count==initial_stock+1,"touch purchase debits once and grants real inventory")
	check(shop.flights.size()==1,"purchase flies to bag after persistence")
	var replay: Dictionary = {"type":"shop_purchase","offer_id":"belt","expected_sequence":0}
	check(not app._shop_purchase(replay,Rect2()).ok and data_item("belt-tile").count==initial_stock+1,"replayed native input cannot buy twice")
	await create_timer(.55).timeout;check(shop.flights.size()==1,"approved 1.1-second flight remains at midpoint");await capture("03-purchase-flight")
	await tap(shop.bag_button);await frames()
	check(not shop.visible and app.editor_ui.is_visible_in_tree(),"bag tap closes Shop and returns inventory")
	check(shop.flights.is_empty() and app.session.snapshot().coins==1200,"closing during flight keeps payment once")
	check(app.session.snapshot().camera==original.state.camera and app.session.save_data().state.editor==original.state.editor,"camera and full tray state restored exactly")
	check(app.editor_ui.scroll_offsets.layout==scroll,"horizontal inventory scroll restored")
	check(app.get_viewport().gui_get_focus_owner()==app.editor_ui.shop,"Shop opener focus restored")
	await capture("04-returned-inventory")
	check(app.session.command({"type":"editor_place","inventory_id":"stool-plain","x":0,"y":5}).ok,"accepted editor can place owned Shop kind")
	check(app.session.command({"type":"editor_remove","id":app.session.snapshot().editor.selected_id}).ok,"accepted Return stores it")
	await tap(app.editor_ui.shop);await frames()
	# A catalog drag starting on a price must scroll, never buy.
	point = shop.rows.belt.buy.get_global_rect().get_center();var before_drag: Dictionary = app.session.save_data()
	await touch(point,true)
	var drag := InputEventScreenDrag.new();drag.index = 18;drag.position = app.get_viewport_transform()*(point-Vector2(0,100));drag.relative = app.get_viewport_transform().basis_xform(Vector2(0,-100));Input.parse_input_event(drag);await frames();await touch(point-Vector2(0,100),false)
	check(app.session.save_data()==before_drag and shop.catalog.scroll_vertical>0,"scrolling from a price never buys")
	shop.catalog.scroll_vertical = 0;await frames()
	point = shop.rows.belt.buy.get_global_rect().get_center();await touch(point,true);await touch(point,false,true)
	check(app.session.save_data()==before_drag,"canceled purchase press changes no state")
	# System Back returns to the same tray without changing the save.
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames();check(not shop.visible and app.session.save_data()==before_drag,"system Back closes Shop read-only")
	await tap(app.editor_ui.shop);await frames()
	var key := InputEventKey.new();key.keycode = KEY_TAB;key.pressed = true;Input.parse_input_event(key);await frames()
	check(shop.is_ancestor_of(app.get_viewport().gui_get_focus_owner()),"keyboard focus stays in Shop")
	shop.bag_button.grab_focus();key = InputEventKey.new();key.keycode = KEY_ENTER;key.pressed = true;Input.parse_input_event(key);await frames();key.pressed=false;Input.parse_input_event(key);await frames()
	check(not shop.visible and app.editor_ui.is_visible_in_tree(),"keyboard bag returns to inventory")
	await tap(app.editor_ui.shop);await frames();app.world.reduced_motion = true;app._refresh()
	app._shop_purchase({"type":"shop_purchase","offer_id":"stool","expected_sequence":app.session.snapshot().shop.purchase_sequence},shop.rows.stool.preview.get_global_rect())
	check(shop.flights.is_empty(),"reduced motion omits travel without losing purchase")
	app.world.reduced_motion = false;app._refresh()
	var stable: Dictionary = app.session.save_data();check(Session.new().restore(JSON.parse_string(JSON.stringify(stable))),"actual native purchases restore")
	# Finite offers use real commands; sold-out cost stays readable and disabled.
	for id in ["plant","plant","barrel"]: app._shop_purchase({"type":"shop_purchase","offer_id":id,"expected_sequence":app.session.snapshot().shop.purchase_sequence},shop.rows[id].preview.get_global_rect())
	shop.cancel_interactions();await frames();shop.catalog.scroll_vertical = 10000;await frames()
	check(shop.rows.plant.buy.disabled and shop.rows.plant.stock.text=="Sold out" and shop.rows.plant.buy.text=="180","sold out retains its cost")
	await capture("05-sold-out")
	shop.dismiss();app.session = Session.new_session(19,{"starting_coins":24});app.session.command({"type":"set_mode","mode":"edit"});app._refresh();await tap(app.editor_ui.shop);await frames()
	for id in shop.rows: check(shop.rows[id].buy.disabled and not shop.rows[id].buy.text.is_empty(),"unaffordable offer visible with cost "+id)
	await capture("06-poor")
	# The gameplay component is also the Shared renderer.
	app.show_gallery = true;app.world.show_gallery = true;await capture("07-shared-shop")
	shop.dismiss();app.show_gallery = false;app.world.show_gallery = false
	app.session = Session.new_session(20,{"starting_coins":1240});app.session.command({"type":"set_mode","mode":"edit"});app._refresh();await tap(app.editor_ui.shop);await frames()
	var original_store = app.store
	var obstacle := "user://shop-write-obstacle-%s" % OS.get_process_id()
	var blocker := FileAccess.open(obstacle,FileAccess.WRITE);blocker.store_string("file blocks save directory");blocker.close()
	app.store = preload("res://scripts/save_store.gd").new(obstacle)
	app._shop_purchase({"type":"shop_purchase","offer_id":"belt","expected_sequence":0},shop.rows.belt.preview.get_global_rect());await frames()
	check(app.save_blocked and shop.flights.is_empty() and not app.pending_shop_receipt.is_empty(),"storage failure blocks further purchases and pending animation")
	check(app.session.snapshot().coins==1200,"failed storage retains one pending debit in memory")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle));app._retry_restore();await frames()
	check(not app.save_blocked and app.pending_shop_receipt.is_empty() and shop.flights.size()==1,"Retry saves the same purchase before animation")
	check(app.store.load_session().state.shop.purchase_sequence==1,"retried purchase is durable")
	app.store = original_store
	# Interrupted touches and animation never commit another purchase on resume.
	shop.cancel_interactions();var paused: Dictionary = app.session.save_data();point = shop.rows.stool.buy.get_global_rect().get_center();await touch(point,true);app.notification(Node.NOTIFICATION_APPLICATION_PAUSED);await touch(point,false);app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);await frames()
	check(app.session.save_data()==paused,"background/resume cancels press ownership")
	var record := {"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":count,"failures":failures}
	if not output.is_empty(): FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE).store_string(JSON.stringify(record,"  "))
	app.audio.set_muted(true);app.audio._music.stop();await create_timer(.15).timeout
	app.queue_free();await frames();await create_timer(.1).timeout;print("Shop native: %s checks, %s failures" % [count,failures.size()]);quit(0 if failures.is_empty() else 1)
