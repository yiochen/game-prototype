extends SceneTree
## Uses the production scene and production Staff presentation in an isolated project.
var app
var destination := ""
func _initialize() -> void: call_deferred("run")
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		quit(1);return
	destination=OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	var dimensions:=OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size=Vector2i(int(dimensions[0]),int(dimensions[1]))
	app=load("res://main.tscn").instantiate();app.show_editor_gallery=true;app.simulation_enabled=false;root.add_child(app)
	await process_frame;await process_frame
	app.show_editor_gallery=false;app.show_gallery=false;app.world.show_gallery=false
	app.session=app.Session.new_session(81,{"starting_coins":1000})
	app._refresh();await capture("00-live-without-staff")
	app.session.command({"type":"set_mode","mode":"edit"});app.session.command({"type":"editor_layer","layer":"people"});app._refresh()
	await capture("01-people-tray")
	app.staff_ui.open_applicants();await create_timer(.4).timeout
	await capture("02-applicants")
	app.staff_ui.browse(1);await create_timer(.7).timeout
	await capture("03-mateo")
	app.staff_ui.cards.values()[1].hire_button.pressed.emit()
	var motion:Array=get_processed_tweens()
	for tween in motion:tween.pause()
	for tween in motion:tween.custom_step(.15)
	await capture("04-hire-expand")
	for tween in motion:tween.custom_step(.255)
	await capture("05-stamp-contact")
	for tween in motion:tween.custom_step(.355)
	await capture("06-hired-imprint")
	for tween in motion:tween.custom_step(.7)
	await capture("07-roster-full")
	var hired_save:Dictionary=app.session.save_data()
	app.staff_ui.dismiss(true)
	app.editor_ui.scroll_by(400);app.editor_ui.commit_scroll()
	await capture("08-new-chef")
	var id:String=app.session.snapshot().staff.hired.keys()[0]
	app._open_recipes(id);app.recipe_ui.inspect("salmon_nigiri");await capture("09-unplaced-recipes")
	app.recipe_ui.dismiss()
	app.session=app.Session.new_session(81,{"starting_coins":30});app._refresh();app.staff_ui.open_applicants();await create_timer(.4).timeout
	await capture("10-poor")
	app.show_gallery=true;app.world.show_gallery=true;app._refresh()
	await capture("11-shared-applicants")
	app.staff_ui.dismiss(true);app.session.restore(hired_save);app._refresh();app.editor_ui.scroll_by(1000*app.editor_ui.unit);app.editor_ui.commit_scroll();await capture("12-shared-new-chef")
	var file:=FileAccess.open(destination.path_join("renderer.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"device":RenderingServer.get_video_adapter_name(),"window":[root.size.x,root.size.y]},"\t"));file.close()
	app.queue_free();await process_frame;quit()
func capture(name:String) -> void:
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name+".png"))
	print("Rendered "+name)
