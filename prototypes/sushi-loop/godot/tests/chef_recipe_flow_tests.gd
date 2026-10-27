extends SceneTree
## Production touch flow: direct recipes, unplaced read-only mode, deferred dots.
const Session = preload("res://scripts/session.gd")
var app
var checks := 0
var failures: Array[String] = []
var output := ""
func _initialize() -> void:call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:failures.append(message);printerr("FAIL: " + message)
func frames() -> void:
	for i in range(3):await process_frame
func touch(at: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new();event.index=34;event.position=app.get_viewport_transform()*at;event.pressed=pressed;Input.parse_input_event(event);await frames()
func tap(control: Control) -> void:
	var at:=control.get_global_rect().get_center();await touch(at,true);await touch(at,false)
func stock(id: String) -> Dictionary:
	return app.session.snapshot().inventory.filter(func(item):return item.id==id)[0]
func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name()=="headless":return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	var size_parts:=OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if size_parts.size()==2:root.size=Vector2i(int(size_parts[0]),int(size_parts[1]))
	output=OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty():DirAccess.make_dir_recursive_absolute(output)
	app=load("res://main.tscn").instantiate();app.show_editor_gallery=true;app.simulation_enabled=false;root.add_child(app);await frames()
	app.session=Session.new_session(81,{"starting_coins":1000});app._refresh();app._layout();await frames()
	await tap(app.edit);await tap(app.editor_ui.layers.people)
	await tap(app.editor_ui.cards[0])
	check(app.recipe_ui.visible and not app.staff_ui.modal.visible,"A placed photo opens Recipes directly with no profile screen")
	app.recipe_ui.inspect("cucumber_maki");await frames()
	check(app.recipe_ui.prepare_button.visible and not app.recipe_ui.prepare_button.disabled,"A placed chef retains explicit Prepare")
	await capture("01-placed-recipes")
	await tap(app.recipe_ui.close_button)
	var result:Dictionary=app._staff_command({"type":"hire_applicant","offer_id":app.session.snapshot().staff.offers[1].id})
	var id:String=result.chef_id
	app.staff_ui._collect_seen(true)
	await tap(app.editor_ui.layers.people) # close without revealing the offscreen new chef
	check(stock(id).staff_new,"Closing People leaves an unseen offscreen chef unread")
	await tap(app.editor_ui.layers.people)
	app.editor_ui.reveal_card(app.editor_ui.cards[-1]);await frames();app.staff_ui._collect_seen(true)
	await create_timer(1.6).timeout
	check(stock(id).staff_new and app.editor_ui.cards[-1].get_meta("new_dot").visible,"The visible dot does not expire in real time")
	await capture("02-new-dot-stays")
	await tap(app.editor_ui.cards[-1])
	check(app.recipe_ui.visible and not app.staff_ui.modal.visible and app.recipe_ui.chef_id==id,"Unplaced photo opens the same Recipes dialog directly")
	app.recipe_ui.inspect("salmon_nigiri");await frames()
	check(not app.recipe_ui.tiles.is_empty() and app.recipe_ui.detail_name.text=="Salmon nigiri","Unplaced staff can browse complete recipe information")
	check(not app.recipe_ui.prepare_button.visible and app.recipe_ui.prepare_button.disabled and not app.recipe_ui.preparing_label.visible,"Unplaced recipes have neither Prepare nor a false preparing status")
	check(stock(id).staff_new,"Inspecting recipes keeps the dot until People closes")
	var unchanged:Dictionary=app.session.save_data()
	app.recipe_ui.prepare_button.pressed.emit()
	check(app.session.save_data()==unchanged,"Hidden Prepare cannot emit a preparation action")
	var rejected:Dictionary=app.session.command({"type":"prepare_recipe","chef_id":id,"recipe_id":"salmon_nigiri"})
	check(not rejected.ok and rejected.reason=="chef_unassigned" and app.session.save_data()==unchanged,"The public command rejects unplaced preparation atomically")
	await capture("03-unplaced-recipes-no-prepare")
	await tap(app.recipe_ui.close_button)
	check(stock(id).staff_new,"Closing Recipes alone retains the dot in the open tray")
	await tap(app.editor_ui.layers.floor)
	check(not stock(id).staff_new,"Switching tabs clears viewed chefs' dots")
	var reopened=Session.new();check(reopened.restore(JSON.parse_string(JSON.stringify(app.session.save_data()))) and not reopened.snapshot().inventory.filter(func(item):return item.id==id)[0].staff_new,"Deferred acknowledgement survives save/reopen")
	await tap(app.editor_ui.layers.people)
	app.editor_ui.reveal_card(app.editor_ui.cards[-1]);await frames()
	check(not app.editor_ui.cards[-1].get_meta("new_dot").visible,"Reopening People shows the acknowledged photo without a dot")
	# A second controlled session verifies the active-tab close action too.
	app.session=Session.new_session(82,{"starting_coins":1000});app._refresh()
	app._editor_command({"type":"set_mode","mode":"edit"});app._editor_command({"type":"editor_layer","layer":"people"})
	result=app._staff_command({"type":"hire_applicant","offer_id":app.session.snapshot().staff.offers[1].id});id=result.chef_id
	app.editor_ui.reveal_card(app.editor_ui.cards[-1]);await frames();app.staff_ui._collect_seen(true)
	check(stock(id).staff_new,"A viewed chef stays unread before tray closure")
	await tap(app.editor_ui.layers.people)
	check(not app.editor_ui.tray.visible and not stock(id).staff_new,"Closing the People tray clears its viewed dots")
	app._editor_command({"type":"editor_layer","layer":"people"})
	app._staff_command({"type":"staff_place","inventory_id":id,"x":1,"y":5})
	app.recipe_ui.inspect("salmon_nigiri");await frames()
	check(app.recipe_ui.visible and app.recipe_ui.prepare_button.visible and not app.recipe_ui.prepare_button.disabled,"Placing the chef enables Prepare in the same dialog")
	await capture("04-placed-idle-can-prepare")
	app.recipe_ui.dismiss();app.queue_free();await frames()
	print("Chef recipes and deferred dots: %s checks, %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
