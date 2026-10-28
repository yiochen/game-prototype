extends SceneTree
const Session=preload("res://scripts/session.gd")
var app
var count:=0
var failures:Array[String]=[]
var output:=""
func _initialize()->void:call_deferred("run")
func check(value:bool,message:String)->void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func frames()->void:
	for i in range(3):await process_frame
func touch(at:Vector2,pressed:bool)->void:
	var e:=InputEventScreenTouch.new();e.index=41;e.position=app.get_viewport_transform()*at;e.pressed=pressed;Input.parse_input_event(e);await frames()
func tap(control:Control)->void:
	var p:=control.get_global_rect().get_center();await touch(p,true);await touch(p,false)
func capture(name:String)->void:
	if output.is_empty() or DisplayServer.get_name()=="headless":return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func run()->void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	var dimensions:=OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size()==2:root.size=Vector2i(int(dimensions[0]),int(dimensions[1]))
	output=OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty():DirAccess.make_dir_recursive_absolute(output)
	app=load("res://main.tscn").instantiate();app.show_editor_gallery=true;app.simulation_enabled=false;root.add_child(app);await frames()
	app.show_editor_gallery=false;app.show_gallery=false;app.world.show_gallery=false
	app.session=Session.new_session(81,{"starting_coins":1240});app._refresh();app._layout()
	app._editor_command({"type":"set_mode","mode":"edit"});app._editor_command({"type":"editor_layer","layer":"people"});await frames()
	await tap(app.editor_ui.cards[0]);var picker=app.recipe_ui;var id:String=picker.chef_id
	check(picker.visible and picker.tab=="recipes","photo opens Recipes directly")
	check(not picker.level_label.visible and picker.recipe_tab.visible and picker.manage_tab.visible,"tabs replace level/Manage shortcut")
	await capture("01-recipes")
	picker.inspect("salmon_nigiri");var offset:int=picker.catalog.scroll_vertical
	await tap(picker.manage_tab);await create_timer(.3).timeout
	check(picker.tab=="manage" and picker.manage_view.visible and not picker.recipe_page.visible,"Manage slides into the fixed popup")
	check(absf(picker.portrait.position.y+picker.portrait.size.y-picker.separator.position.y)<.01 and picker.separator.visible,"headshot touches the Manage separator")
	var manage=picker.manage_view;var before:Dictionary=app.session.save_data()
	await tap(manage.upgrade);check(app.session.snapshot().coins==int(before.state.coins)-60,"native upgrade pays one level")
	check(manage.actor.level==2 and manage.actor.cooking_speed>1,"native stats update in place")
	await capture("02-manage-unlock-preview")
	await create_timer(.35).timeout
	var p:Vector2=manage.upgrade.get_global_rect().get_center();await touch(p,true);await capture("03-upgrade-pressed");await touch(p,false);await create_timer(.1).timeout
	check(manage.actor.level==3,"Yellow threshold bought through touch")
	await tap(picker.recipe_tab);await create_timer(.3).timeout
	check(picker.selected=="salmon_nigiri" and picker.catalog.scroll_vertical==offset,"tabs preserve inspected recipe and scroll")
	await tap(picker.manage_tab);await create_timer(.3).timeout
	await tap(manage.unassign);check(not manage.placed() and manage.actor.level==3,"unassign preserves upgraded chef")
	await tap(picker.recipe_tab);await create_timer(.3).timeout
	check(not picker.prepare_button.visible and picker.prepare_button.disabled,"stored chef Recipes has no Prepare")
	await tap(picker.manage_tab);await create_timer(.3).timeout
	await tap(manage.unassign);check(not picker.visible and not app.armed_item.is_empty(),"Place in restaurant arms existing valid placement")
	app.armed_item.clear();app.editor_ui.active_item=""
	var placed:Dictionary=app._staff_command({"type":"staff_place","inventory_id":id,"x":1,"y":5});await frames()
	check(placed.ok and picker.visible and picker.tab=="recipes","reassignment opens shared recipe picker")
	await tap(picker.manage_tab);await create_timer(.3).timeout
	await tap(manage.fire);await create_timer(.4).timeout
	check(picker.dismissal.visible and picker.dismissal.resume.offer.art_id==manage.actor.art_id,"Fire slides up the same chef application")
	await capture("04-fire-application")
	var cancel_save:Dictionary=app.session.save_data();await tap(picker.dismissal.cancel_button)
	check(not picker.dismissal.visible and app.session.save_data()==cancel_save,"Cancel preserves exact state")
	await tap(manage.fire);await create_timer(.4).timeout
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames()
	check(not picker.dismissal.visible and picker.visible and app.session.save_data()==cancel_save,"system Back cancels the named firing confirmation")
	app.staff_ui.viewed_chefs[id]=true
	await tap(manage.fire);await create_timer(.4).timeout;await tap(picker.dismissal.confirm_button);await create_timer(.4).timeout
	check(picker.dismissal.fired and not app.session.snapshot().inventory.any(func(c):return c.id==id),"confirm commits dismissal before stamp finishes")
	check(not app.staff_ui.viewed_chefs.has(id),"fired chef is removed from pending seen acknowledgements")
	await capture("05-fired-stamp-contact");await create_timer(.8).timeout
	check(picker.dismissal.visible and picker.dismissal.resume.imprint.modulate.a>.9 and picker.dismissal.resume.stamp_text.text=="Fired","Fired ink remains on application")
	await capture("06-fired-retained")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(app.session.save_data()))),"native firing save reopens")
	await tap(picker.dismissal.cancel_button);check(not picker.visible,"Close leaves the dismissed chef removed")
	check(app.editor_ui.layers.people.visible and app.editor_ui.layers.layout.visible and app.editor_ui.layers.floor.visible and app.editor_ui.live.visible,"Edit categories and Live remain after dialogs")
	# Same production component in its Shared host: poor and MAX retain information.
	app.session=Session.new_session(82,{"starting_coins":0});app._refresh();app._open_recipes(id);picker.switch_tab("manage",false);await frames()
	check(manage.upgrade.disabled and not manage.budget.text.is_empty(),"insufficient funds retain preview and cost")
	await capture("07-poor")
	app.session=Session.new_session(82,{"starting_coins":10000})
	for level in range(1,12):app.session.command({"type":"level_up_chef","chef_id":id,"expected_level":level})
	app._refresh();picker.switch_tab("manage",false);await frames()
	check(not manage.upgrade.visible and "MAX" in manage.next_label.text,"MAX retains final level and stats without price")
	await capture("08-max");app.show_gallery=true;app.world.show_gallery=true;await capture("09-shared-manage")
	app._open_recipes("chef-disconnected");picker.switch_tab("manage",false);picker.open_firing();await frames()
	check(picker.dismissal.resume.offer.name=="Mina","a shared art identity never replaces the chef name on the application")
	picker.dismissal.back();picker.dismiss()
	# A real filesystem write failure pauses presentation until Retry saves removal.
	app.show_gallery=false;app.show_editor_gallery=false
	var original_store=app.store
	var obstacle:="user://chef-write-obstacle-%s"%OS.get_process_id()
	var blocker:=FileAccess.open(obstacle,FileAccess.WRITE);blocker.store_string("file blocks the save directory");blocker.close()
	app._open_recipes("chef-disconnected");picker.switch_tab("manage",false);picker.open_firing();await frames()
	app.store=preload("res://scripts/save_store.gd").new(obstacle)
	app._manage_chef({"type":"fire_chef","chef_id":"chef-disconnected"})
	check(app.save_blocked and not picker.dismissal.fired,"failed save blocks the firing receipt until persistence succeeds")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle));app._retry_restore();await frames()
	check(not app.save_blocked and picker.dismissal.fired,"Retry resumes the Fired receipt after saving the same removal")
	check(app.store.load_session().state.staff.dismissed.has("chef-disconnected"),"retried firing is durable")
	picker.dismissal.back();app.store=original_store
	var record:={"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"adapter":RenderingServer.get_video_adapter_name(),"checks":count,"failures":failures}
	if not output.is_empty():var f:=FileAccess.open(output.path_join("renderer.json"),FileAccess.WRITE);f.store_string(JSON.stringify(record,"  "))
	app.queue_free();await frames();print("Chef development native: %s checks, %s failures"%[count,failures.size()]);quit(0 if failures.is_empty() else 1)
