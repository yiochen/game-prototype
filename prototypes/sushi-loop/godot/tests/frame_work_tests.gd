extends SceneTree
class CountedSession extends "res://scripts/session.gd":
	var snapshot_calls := 0
	func snapshot() -> Dictionary:
		snapshot_calls += 1
		return super.snapshot()

func _initialize() -> void: call_deferred("run")
func run() -> void:
	assert(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"))
	root.size = Vector2i(390, 844)
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	app.set_process(false)
	var counted := CountedSession.new()
	counted._configuration = app.session._configuration
	counted._editor_content = app.session._editor_content
	counted._state = app.session._state
	counted._random = app.session._random
	counted._access_paths = app.session._access_paths
	app.session = counted
	app._process(1.0 / 60.0)
	assert(counted.snapshot_calls == 1, "A Live frame must prepare exactly one detached snapshot")
	assert(app.world.state == counted.snapshot(), "Visible state must include the latest simulation step")
	counted.snapshot_calls = 0
	app.advance_time(1.0 / 60.0)
	assert(counted.snapshot_calls == 1, "Explicit time advancement must still refresh immediately for tools and tests")
	assert(app.world.state == counted.snapshot())
	app.queue_free()
	await process_frame
	print("Frame work checks passed: one snapshot per Live frame, explicit advance still refreshes")
	quit()
