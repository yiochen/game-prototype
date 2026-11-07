extends SceneTree
const Session=preload("res://scripts/session.gd")
const Book=preload("res://scripts/floor_book.gd")
var app
var count:=0
var failures:Array[String]=[]
var output:=""
func _initialize()->void:call_deferred("run")
func check(value:bool,message:String)->void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func frames()->void:
	for i in range(4):await process_frame
func touch(at:Vector2,pressed:bool,canceled:=false)->void:
	var e:=InputEventScreenTouch.new();e.index=20;e.position=app.get_viewport_transform()*at;e.pressed=pressed;e.canceled=canceled;Input.parse_input_event(e);await frames()
func drag(at:Vector2)->void:
	var e:=InputEventScreenDrag.new();e.index=20;e.position=app.get_viewport_transform()*at;Input.parse_input_event(e);await frames()
func tap(control:Control)->void:
	var at:=control.get_global_rect().get_center();await touch(at,true);await touch(at,false)
func capture(name:String)->void:
	if output.is_empty() or DisplayServer.get_name()=="headless":return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func card(id:String)->Button:
	for c in app.editor_ui.cards:
		if c.get_meta("entry").id==id:return c
	return null
func cell(x:int,y:int)->Vector2:return app.world.cell_base(x,y)
func run()->void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	var dimensions:=OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size()==2:root.size=Vector2i(int(dimensions[0]),int(dimensions[1]))
	output=OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty():DirAccess.make_dir_recursive_absolute(output)
	app=load("res://main.tscn").instantiate();app.show_editor_gallery=true;app.simulation_enabled=false;root.add_child(app);await frames()
	app.show_editor_gallery=false;app.show_gallery=false;app.world.show_gallery=false
	app.session=Session.new_session(20,{"starting_coins":1240})
	var fixture:Dictionary=GameSession.flat_view(app.session.save_data())
	fixture.state.floor_styles.owned=["jade","terracotta","checker","petal","linen","cream"];fixture.state.floor_styles.purchase_sequence=5;fixture.state.floor_styles.offer="blue-wave"
	check(app.session.restore(fixture),"gallery collection fixture uses valid save boundary")
	app._editor_command({"type":"set_mode","mode":"edit"});app._editor_command({"type":"editor_layer","layer":"floor"});app._refresh();app._layout();await frames()
	# Keep a playable floor in very short landscape containment.
	if root.size.x>root.size.y:app._pan(Vector2(0,-3*app.world.cell));await frames()
	check(app.floor_ui.visible and app.floor_ui.instruction.text=="select a tile pattern","Floor starts without brush and shows centered prompt")
	check(app.editor_ui.cards.size()==6,"owned style thumbnails populate scroll strip")
	for c in app.editor_ui.cards:
		check(not c.disabled and not c.get_meta("name_label").visible and not c.get_meta("stock").visible,"thumbnail only, no captions/stock")
	await capture("01-palette")
	var original:Dictionary=GameSession.flat_view(app.session.save_data());var p:Vector2=card("petal").get_global_rect().get_center()
	await touch(p,true);check(app.floor_ui.instruction.visible,"palette down keeps selection instruction visible")
	await drag(p-Vector2(140*app.editor_ui.unit,0));check(app.floor_ui.instruction.visible,"palette scroll keeps instruction visible");await capture("02-scrolling-instruction");await touch(p-Vector2(140*app.editor_ui.unit,0),false)
	check(app.session.snapshot().floor_styles.painted==original.state.floor_styles.painted and app.session.snapshot().floor_styles.owned==original.state.floor_styles.owned and app.session.snapshot().camera==original.state.camera,"palette scroll cannot paint or pan")
	check(app.session.snapshot().editor.get("floor_brush","")=="","palette scroll cannot select brush")
	card("cream").grab_focus();await frames()
	var key:=InputEventKey.new();key.keycode=KEY_ENTER;key.pressed=true;Input.parse_input_event(key);await frames();key.pressed=false;Input.parse_input_event(key);await frames()
	check(app.session.snapshot().editor.get("floor_brush","")=="cream","keyboard selection still works immediately after touch scrolling")
	app._floor_select("")
	app.editor_ui.scroll_by(-10000);await frames();await tap(card("jade"));await frames()
	check(app._painting_floor() and app.floor_ui.instruction.text=="paint the floor","tap selects unlimited brush and changes prompt")
	check(app.world.painting_floor(),"native world enters translucent painting mode")
	p=card("petal").get_global_rect().get_center();await touch(p,true);await drag(p-Vector2(100*app.editor_ui.unit,0))
	check(app.floor_ui.instruction.visible and app.floor_ui.instruction.text=="paint the floor","selected-brush palette scrolling keeps painting instruction visible")
	await capture("03b-selected-palette-scrolling");await touch(p-Vector2(100*app.editor_ui.unit,0),false)
	check(app.session.snapshot().editor.floor_brush=="jade","palette scrolling preserves active brush")
	app.editor_ui.scroll_by(-10000);await frames()
	await capture("03-brush-selected")
	p=app.floor_ui.exit_button.get_global_rect().get_center();await touch(p,true);app.notification(Node.NOTIFICATION_APPLICATION_PAUSED);await touch(p,false);app.notification(Node.NOTIFICATION_APPLICATION_RESUMED);await frames()
	check(app.session.snapshot().editor.get("floor_brush","")=="jade","background cancels a held brush-exit X without an orphan action")
	p=cell(3,5);await touch(p,true);check(not app.floor_ui.instruction.visible,"scene touch hides painting instruction");await capture("04-touch-down");await drag(cell(5,5));await touch(cell(5,5),false)
	check(app.session.snapshot().floor_styles.painted.get("4,5")=="jade","fast stroke paints crossed cells")
	check(app.floor_ui.instruction.visible,"scene release restores instruction")
	p=cell(2,6);await touch(p,true);await touch(p,false)
	check(app.session.snapshot().floor_styles.painted.get("2,6")=="jade","objects do not intercept painting beneath the belt")
	await capture("05-painted-under-furniture")
	var painted:Dictionary=app.session.snapshot().floor_styles.painted.duplicate(true)
	var camera:Dictionary=app.session.snapshot().camera.duplicate(true)
	await tap(app.floor_ui.carets.right);await frames()
	check(app.session.snapshot().camera.x>camera.x and app.session.snapshot().floor_styles.painted==painted and app._painting_floor(),"scene caret pans without painting or clearing brush")
	# Panning brings actual trash footprints into view without replacing the scene.
	app._pan(Vector2(-4*app.world.cell,0));await frames()
	if root.size.x>root.size.y:app._pan(Vector2(0,app.world.cell));await frames()
	p=cell(7,4);await touch(p,true);await touch(p,false)
	check(not app.session.snapshot().floor_styles.painted.has("7,4"),"trash-covered floor cannot be painted")
	check(not app.clearance_ui.visible,"brush tap never opens trash inspection")
	await capture("06-trash-blocked")
	await tap(app.editor_ui.layers.floor);check(app._painting_floor() and not app.session.snapshot().editor.tray_open,"palette collapse retains brush")
	await capture("07-collapsed-palette");await tap(app.editor_ui.layers.floor)
	await tap(app.floor_ui.exit_button);await frames()
	check(not app._painting_floor() and app.session.snapshot().editor.layer=="floor" and app.session.snapshot().editor.tray_open,"X clears brush but retains Floor/palette")
	check(not app.world.painting_floor() and app.floor_ui.instruction.text=="select a tile pattern","X restores opaque objects and select prompt")
	await capture("08-brush-exit")
	var before_shop:Dictionary=app.session.snapshot();await tap(app.editor_ui.shop);await frames()
	check(app.shop_ui.visible and not app.floor_ui.visible,"Shop hides paint controls")
	var shop=app.shop_ui;shop.catalog.scroll_vertical=0;await frames();await capture("09-pattern-offer")
	await tap(shop.rows["floor:blue-wave"].buy);await frames()
	check(app.session.snapshot().coins==640 and app.session.snapshot().floor_styles.owned[0]=="blue-wave","native purchase debits once and prepends style")
	check(shop.visible and shop.rows["floor:blue-wave"].owned.visible and not shop.rows["floor:blue-wave"].buy.visible,"purchase stays in Shop with noninteractive Owned")
	check(app.clearance_toast.visible and app.clearance_toast.text=="Blue Wave unlocked","named unlock toast after persistence")
	await capture("10-pattern-owned")
	await tap(shop.bag_button);await frames();check(app.session.snapshot().camera==before_shop.camera,"Shop return keeps scene camera")
	check(app.editor_ui.cards.size()==7,"new style joins same native palette")
	app._show_clearance_notice("Clear trash before painting here.")
	check(app.clearance_toast.size.x>=app.world.hud_area().size.x*.8,"trash notice restores its full readable width after a compact unlock toast")
	app.clearance_toast.hide()
	app.editor_ui.reveal_card(card("blue-wave"));await frames();await tap(card("blue-wave"));await frames();await capture("11-new-pattern-selected")
	check(app.session.snapshot().editor.floor_brush=="blue-wave","purchased style is usable")
	await tap(app.editor_ui.shop);await frames();check(not app.world.painting_floor() and app.session.snapshot().editor.floor_brush=="blue-wave","Shop suspends translucency while retaining brush")
	await tap(app.shop_ui.bag_button);await frames();check(app.world.painting_floor(),"Shop return restores brush translucency")
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames();check(not app._painting_floor() and app.session.snapshot().mode=="edit","system Back exits brush rather than leaving editor")
	var saved:Dictionary=GameSession.flat_view(app.session.save_data());check(app.save_now(),"native painted save persists")
	var replay=Session.new();check(replay.restore(saved) and replay.snapshot().floor_styles.painted==saved.state.floor_styles.painted,"native floor save restores without repainting/redebit")
	for button in app.floor_ui.carets.values()+[app.floor_ui.exit_button]+app.editor_ui.cards:
		var scale_value:float=app.get_viewport_transform().get_scale().x
		check(button.size.x*scale_value>=44 and button.size.y*scale_value>=44,"floor controls >=44px")
	# --floor-gallery uses these same native controls and full-scene renderer.
	app.show_editor_gallery=true;app._floor_select("");app.editor_ui.reveal_card(card("blue-wave"));await frames();await capture("12-shared-floor-normal")
	p=card("blue-wave").get_global_rect().get_center();await touch(p,true);await capture("13-shared-floor-pressed");await touch(p,false);await capture("14-shared-floor-selected")
	app.session.command({"type":"set_camera","x":0,"y":0});app._refresh();await frames();check(app.floor_ui.carets.left.disabled and app.floor_ui.carets.up.disabled,"shared scene disables unavailable pan directions");await capture("15-shared-floor-disabled-carets")
	if not output.is_empty():FileAccess.open(output.path_join("checks.json"),FileAccess.WRITE).store_string(JSON.stringify({"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":count,"failures":failures},"  "))
	print("Floor native: %s checks, %s failures"%[count,failures.size()]);app.queue_free();await frames();quit(0 if failures.is_empty() else 1)
