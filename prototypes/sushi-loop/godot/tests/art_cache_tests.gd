extends SceneTree
## Guards against atlas reload thrash: on a phone every reload is a
## synchronous decode inside _draw. Within budget, an atlas loads once.
var checks := 0
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func _expect(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func _play(app, world, art, frames: int) -> void:
	# The picking pass resolves the same sprites and frames as rendering.
	for _frame in range(frames):
		app.advance_time(1.0 / 20.0)
		art.begin_frame()
		world._ensure_sprite_hits()
		art.end_frame()

func run() -> void:
	await _measure()
	await process_frame
	for failure in failures: print("FAIL: " + failure)
	if failures.is_empty():
		print("PASS: %s art cache checks" % checks)
		quit(0)
	else:
		quit(1)

func _measure() -> void:
	# Locals here hold every loaded atlas; returning releases them before exit.
	root.size = Vector2i(390, 844)
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	app.set_process(false)
	await process_frame
	var world = app.world
	var art = world.art
	art.budget_bytes = 1 << 40
	art.load_counts.clear()
	_play(app, world, art, 1200)
	var repeated: Array = art.load_counts.keys().filter(func(path): return art.load_counts[path] > 1)
	_expect(art.load_counts.size() >= 8, "A minute of service exercises varied clips (%d atlases)" % art.load_counts.size())
	_expect(repeated.is_empty(), "Within budget no atlas loads twice; reloaded: %s" % [repeated])
	# Prove the check has teeth: with no budget, clip changes must reload.
	art.budget_bytes = 0
	art.load_counts.clear()
	_play(app, world, art, 600)
	_expect(art.load_counts.values().any(func(count): return count > 1), "Over budget, dropped atlases are reloaded when drawn again")
	art.sources.clear()
	app.queue_free()
	await process_frame
