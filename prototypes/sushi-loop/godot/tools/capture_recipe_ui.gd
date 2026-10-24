extends SceneTree
## Render review artwork only, using an isolated preview project/save identity.
var app
var destination := ""
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty() or not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopRecipePreview"):
		printerr("An isolated recipe preview project and capture directory are required.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.show_editor_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	await process_frame
	app.session.command({"type":"editor_layer", "layer":"people"})
	app._refresh()
	await capture("01-people-instant-photos")
	app._open_recipes("chef-1")
	await capture("02-current-recipe")
	app.recipe_ui.inspect("cucumber_maki")
	await capture("03-inspected-recipe")
	app._prepare_recipe("chef-1", "cucumber_maki")
	await capture("04-changed-blackboard")
	app.session.command({"type":"set_mode", "mode":"live"})
	app.advance_time(14.05)
	await capture("04b-held-cucumber")
	app.advance_time(1.05)
	await capture("04c-loaded-cucumber")
	app.session.command({"type":"set_mode", "mode":"edit"})
	app._refresh()
	var data: Dictionary = app.session.save_data()
	for actor in data.state.objects:
		if actor.kind == "chef" and actor.id == "chef-1": actor.level = 5
	for stock in data.state.inventory:
		if stock.id == "chef-1": stock.level = 5
	app.session.restore(data)
	app.session.command({"type":"discover_recipe", "recipe_id":"eel_roll"})
	app.session.command({"type":"discover_recipe", "recipe_id":"tamago_nigiri"})
	app._refresh()
	app._open_recipes("chef-1")
	await capture("05-discovered-new")
	app.recipe_ui.inspect("eel_roll")
	await capture("06-eligible-details")
	app.recipe_ui.inspect("unknown-Black")
	await capture("07-unknown-no-price")
	app.recipe_ui.dismiss()
	app._open_recipes("chef-2")
	app.recipe_ui.inspect("eel_roll")
	await capture("08-ineligible-details")
	app.recipe_ui.dismiss()
	data = app.session.save_data()
	for actor in data.state.objects:
		if actor.kind == "chef" and actor.id == "chef-2":
			actor.recipe_id = ""
			actor.held_dish = null
			actor.preparation_elapsed = 0.0
			actor.visual_phase = "idle"
	for stock in data.state.inventory:
		if stock.id == "chef-2": stock.recipe_id = ""
	app.session.restore(data)
	app._open_recipes("chef-2")
	await capture("09-idle-no-selection")
	app.recipe_ui.dismiss()
	app.show_gallery = true
	app.world.show_gallery = true
	app._refresh()
	app._open_recipes("chef-1")
	app.recipe_ui.inspect("tamago_nigiri")
	await capture("10-shared-native-picker")
	var renderer := {"renderer":RenderingServer.get_current_rendering_method(), "driver":RenderingServer.get_current_rendering_driver_name(), "device":RenderingServer.get_video_adapter_name(), "window":[root.size.x,root.size.y]}
	var file := FileAccess.open(destination.path_join("renderer.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(renderer,"\t"))
	file.close()
	app.queue_free()
	await process_frame
	quit()
func capture(name: String) -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name+".png"))
	print("Rendered "+name)
