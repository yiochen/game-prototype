extends SceneTree
## Integrated touch, modal, transaction, placement and unread behavior in production UI.
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
var app
var count := 0
var failures:Array[String]=[]
func _initialize() -> void:call_deferred("run")
func check(value:bool,message:String) -> void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func frames() -> void:
	for i in range(3):await process_frame
func touch(at:Vector2,pressed:bool,canceled:=false) -> void:
	var event:=InputEventScreenTouch.new();event.index=21;event.position=app.get_viewport_transform()*at;event.pressed=pressed;event.canceled=canceled;Input.parse_input_event(event);await frames()
func drag(start:Vector2,end:Vector2) -> void:
	var event:=InputEventScreenDrag.new();event.index=21;event.position=app.get_viewport_transform()*end;event.relative=app.get_viewport_transform().basis_xform(end-start);Input.parse_input_event(event);await frames()
func tap(control:Control) -> void:
	var at:=control.get_global_rect().get_center();await touch(at,true);await touch(at,false)
func stock(id:String) -> Dictionary:
	return app.session.snapshot().inventory.filter(func(item):return item.id==id)[0]
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	var dimensions:=OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size()==2:root.size=Vector2i(int(dimensions[0]),int(dimensions[1]))
	app=load("res://main.tscn").instantiate();app.show_editor_gallery=true;app.simulation_enabled=false;root.add_child(app);await frames()
	app.show_editor_gallery=false;app.session=Session.new_session(81,{"starting_coins":1000});app.store=Store.new("user://staff-integration");app.store.clear_session();app.store.load_session(app._valid_saved_session);app._refresh();app._layout();await frames()
	await tap(app.edit);await tap(app.editor_ui.layers.people)
	check(app.editor_ui.visible and app.editor_ui.applicants.visible and app.session.snapshot().mode=="edit","People is the shared roster entry in Edit")
	var origin:Dictionary=app.session.snapshot()
	await tap(app.editor_ui.applicants)
	var ui=app.staff_ui
	check(ui.modal.visible and ui.cards.size()==3,"Applicants opens three persistent paper applications")
	var all_targets:=true
	for control in [ui.close_button,ui.refresh_button,ui.cards.values()[0].hire_button]:
		var physical:Rect2=app.get_viewport_transform()*control.get_global_rect()
		all_targets=all_targets and physical.size.x>=43.99 and physical.size.y>=43.99
	check(all_targets,"Native action targets retain 44 physical pixels")
	check(is_equal_approx(ui.fan.size.x,app.world.portrait.size.x) and ui.fan.clip_contents,"Fan extends to both portrait edges and clips horizontally")
	var camera:Dictionary=app.session.snapshot().camera
	var start:Vector2=ui.fan.get_global_rect().get_center()
	await touch(start,true);await drag(start,start-Vector2(ui.pitch*ui.unit*.9,0));await touch(start-Vector2(ui.pitch*ui.unit*.9,0),false);await create_timer(.7).timeout
	check(ui.active>=1 and absf(ui.position_value-ui.active)<.02,"Actual touch swipe settles onto the next tilted application")
	check(app.session.snapshot().coins==1000 and app.session.snapshot().staff.count==3 and app.session.snapshot().camera==camera,"Browsing cannot hire or pan the restaurant")
	ui.browse(1);await create_timer(.7).timeout
	start=ui.cards.values()[1].hire_button.get_global_rect().get_center()
	await touch(start,true);app.propagate_notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);await touch(start,false)
	check(app.session.snapshot().coins==1000,"Focus loss cancels a held Hire button")
	await tap(ui.cards.values()[1].hire_button)
	check(app.session.snapshot().coins==910 and app.session.snapshot().staff.count==4 and app.session.snapshot().staff.offers.size()==2,"One native Hire commits one debit and removes only its offer")
	if app.session.snapshot().staff.hired.is_empty():
		app.queue_free();await frames();quit(1);return
	var id:String=app.session.snapshot().staff.hired.keys()[0]
	check(stock(id).staff_new and not stock(id).assigned,"New chef is unread and unassigned")
	check(ui.hero!=null and not app.editor_ui.rejection.visible,"Native hire confirmation runs without a toast")
	await create_timer(1.5).timeout
	check(ui.hero==null and ui.modal.visible and ui.subtitle.text.contains("Roster full"),"After the stamp exit the same popup shows remaining offers and red capacity")
	check(ui.cards.values().all(func(card):return card.hire_button.disabled),"Full roster disables remaining Hire actions")
	var before:Dictionary=app.session.save_data()
	await tap(ui.refresh_button)
	check(app.session.snapshot().staff.offers.size()==3 and app.session.snapshot().coins==910 and ui.refresh_button.disabled,"Explicit Refresh is free and starts its persisted real-time cooldown")
	var deadline:float=app.session.snapshot().staff.refresh_deadline
	ui.dismiss(true);app._refresh();await frames()
	check(app.session.snapshot().mode==origin.mode and app.session.snapshot().editor==origin.editor and app.session.snapshot().camera==origin.camera,"Closing applicants restores the originating mode, tray and camera")
	check(stock(id).staff_new,"An offscreen new chef remains unread")
	app.editor_ui.scroll_by(1000*app.editor_ui.unit);app.editor_ui.commit_scroll();app._refresh();await frames()
	check(app.editor_ui.rail.get_global_rect().encloses(app.editor_ui.cards[-1].get_global_rect()),"People tray scroll reveals its complete last photo")
	check(app.editor_ui.cards[-1].get_meta("new_dot").visible,"Unread chef photo carries a red dot")
	ui.open_applicants();await create_timer(1.5).timeout
	check(stock(id).staff_new,"A covering modal never acknowledges the roster photo")
	check(ui.refresh_button.disabled and app.session.snapshot().staff.refresh_deadline==deadline,"Reopening cannot bypass Refresh cooldown")
	ui.dismiss(true)
	ui._collect_seen(true);await create_timer(1.5).timeout
	check(stock(id).staff_new,"Visible dots remain while People stays open")
	app._open_recipes(id);await frames()
	check(app.recipe_ui.visible and not ui.modal.visible and not app.recipe_ui.prepare_button.visible,"Unplaced chef opens Recipes directly without Prepare")
	check(stock(id).staff_new,"Opening Recipes does not clear the dot in real time")
	app.recipe_ui.dismiss();await frames()
	app._editor_command({"type":"editor_layer","layer":"floor"})
	check(not stock(id).staff_new,"Switching away from People acknowledges viewed chefs")
	app._editor_command({"type":"editor_layer","layer":"people"});app._refresh();await frames()
	var destination:=Vector2i(-1,-1)
	for y in range(3,9):
		for x in range(7):
			var probe=Session.new();probe.restore(app.session.save_data())
			var point:Vector2=app.world.cell_base(x,y)
			if app._floor_drop(point) and probe.command({"type":"staff_place","inventory_id":id,"x":x,"y":y}).get("ok",false):destination=Vector2i(x,y);break
		if destination.x>=0:break
	check(destination.x>=0,"An empty visible belt-adjacent cell is reachable from People")
	if destination.x>=0:
		var at:Vector2=app.world.cell_base(destination.x,destination.y)
		app.editor_ui.reveal_card(app.editor_ui.cards[-1]);await frames()
		start=app.editor_ui.cards[-1].get_global_rect().get_center()
		await touch(start,true);await drag(start,start-Vector2(0,60)*app.editor_ui.unit);await drag(start-Vector2(0,60)*app.editor_ui.unit,at);await touch(at,false)
		check(stock(id).assigned and app.recipe_ui.visible and app.recipe_ui.selected=="","People placement immediately opens the idle native recipe picker")
		app.recipe_ui.dismiss();await frames()
		check(stock(id).recipe_id=="","Closing without Prepare leaves the new chef idle")
	check(not app.save_blocked and app.save_now(),"Native hire, refresh, seen and assignment save successfully")
	var reopened=Session.new();check(reopened.restore(app.store.load_session(app._valid_saved_session)) and reopened.snapshot().staff.refresh_deadline==deadline and reopened.snapshot().staff.hired.has(id),"Native file save reopens payment, pool, deadline and identity")
	# The same upward photo gesture also places in paused Edit.
	app.recipe_ui.dismiss()
	app.session=Session.new_session(91,{"starting_coins":1000})
	app.session.command({"type":"set_mode","mode":"edit"});app.session.command({"type":"editor_layer","layer":"people"})
	var recruit:Dictionary=app._staff_command({"type":"hire_applicant","offer_id":app.session.snapshot().staff.offers[1].id})
	id=str(recruit.chef_id);app._refresh();app._layout();app.editor_ui.reveal_card(app.editor_ui.cards[-1]);await frames()
	start=app.editor_ui.cards[-1].get_global_rect().get_center()
	before=app.session.save_data()
	await touch(start,true);await drag(start,start-Vector2(0,60)*app.editor_ui.unit);await touch(start-Vector2(0,60)*app.editor_ui.unit,false,true)
	check(not stock(id).assigned and app.session.save_data().state.objects==before.state.objects and app.session.snapshot().coins==910,"Cancelled upward photo drag preserves staff, debit and arrangement")
	app.armed_item.clear();app.editor_ui.active_item="";app._refresh();await frames()
	start=app.editor_ui.cards[-1].get_global_rect().get_center()
	var at:Vector2=app.world.cell_base(1,5)
	await touch(start,true);await drag(start,start-Vector2(0,60)*app.editor_ui.unit)
	check(app.gesture_kind=="inventory","Upward native photo motion owns placement")
	await drag(start-Vector2(0,60)*app.editor_ui.unit,at);await touch(at,false)
	check(stock(id).assigned and app.recipe_ui.visible and app.recipe_ui.selected=="" and app.session.snapshot().mode=="edit","Edit drag places the same idle chef and opens the shared recipe picker")
	app.recipe_ui.dismiss();app.world.reduced_motion=true
	app.session=Session.new_session(92,{"starting_coins":1000});app._refresh();ui.open_applicants();await frames()
	await tap(ui.cards.values()[0].hire_button);await create_timer(.18).timeout
	check(ui.hero!=null and ui.hero.scale.is_equal_approx(Vector2.ONE) and ui.hero.stamp_prop.modulate.a==0 and ui.hero.imprint.modulate.a>0,"Reduced motion confirms with ink and no physical stamp or expansion")
	app._notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST);await frames()
	check(not ui.modal.visible and app.session.snapshot().staff.count==4,"Android Back closes the confirmation overlay without undoing its committed hire")
	app.queue_free();await frames()
	print("Staff native: %s checks, %s failures" % [count,failures.size()]);quit(0 if failures.is_empty() else 1)
