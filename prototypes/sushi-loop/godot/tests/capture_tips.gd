extends SceneTree
## #61 native review captures: floor cash at each tier (one hidden behind a
## guest), the placed tip jar and its states, a tea request, a toss, a jar
## deposit with its popup, and collection flying to the rolling counter.
##   python3 godot/tools/test_native.py --script tests/capture_tips.gd --visible --resolution 780x1688 --output review/61/native/phone

const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app
var destination := ""
var manifest: Array = []

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41, {"starting_coins": 2000})
	app._refresh()
	for step in range(900): app.advance_time(0.05, false)
	# A bought and placed jar, and one pile per tier; the $15 pile sits behind
	# the guest on the lower belt's stool.
	app.dispatch({"type": "set_mode", "mode": "edit"})
	app.dispatch({"type": "shop_purchase", "offer_id": "tip-jar", "expected_sequence": app.session.snapshot().shop.purchase_sequence})
	app.dispatch({"type": "editor_place", "inventory_id": "tip-jar", "x": 1, "y": 11})
	app.dispatch({"type": "set_mode", "mode": "live"})
	var state: Dictionary = app.session._state
	for pile in [[5, 5, 6], [1, 8, 24], [4, 7, 80], [3, 7, 15], [0, 4, 3]]:
		if app.session._cash_cell_open(Vector2i(pile[0], pile[1])): state.tips.cash.append({"x": pile[0], "y": pile[1], "amount": pile[2]})
	state.tips.jar.balance = 34
	for customer in app.session._customers():
		if customer.phase in ["waiting", "eating"] and customer.first_dish_received:
			customer.tea_phase = "requested"
			customer.tea_elapsed = 2.0
			break
	app._refresh()
	await capture("01-floor-cash-jar-tea")
	# Tea served: the guest thanks with the shared happy bubble.
	for customer in app.session.snapshot().customers:
		if customer.tea_phase == "requested":
			app._tip_tap({"kind": "tea", "customer_id": customer.id})
			break
	await settle(0.6)
	await capture("02-tea-served")
	# A toss onto the floor, mid-arc.
	var tossing: Dictionary = app.session.snapshot().objects.filter(func(o): return o.kind == "seat")[1]
	var target := Vector2i(int(tossing.x) + 1, int(tossing.y) - 1)
	if app.session._cash_cell_open(target):
		state.tips.cash.append({"x": target.x, "y": target.y, "amount": 30})
		app._present_tip_event({"type": "tip", "destination": "floor", "amount": 30, "accepted": 30, "x": target.x, "y": target.y, "from_x": float(tossing.x), "from_y": float(tossing.y)})
	await settle(0.25)
	await capture("03-tip-toss")
	# A deposit flying into the jar, then its popup.
	state.tips.jar.balance = 49
	app._present_tip_event({"type": "tip", "destination": "jar", "amount": 15, "accepted": 15, "x": 1, "y": 11, "from_x": 3.0, "from_y": 8.0, "full": false})
	await settle(0.35)
	await capture("04-jar-flight")
	await settle(0.55)
	await capture("05-jar-gain")
	# Collecting the bundle (and its neighbour) flies cash to the counter.
	app._tip_tap({"kind": "cash", "x": 4, "y": 7})
	await settle(0.3)
	await capture("06-collect-flight")
	await settle(0.9)
	await capture("07-counter-after")
	# A full jar.
	state.tips.jar.balance = 100
	app._refresh()
	await settle(0.1)
	await capture("08-jar-full")
	# Edit: cash stays on the floor, and the jar is an ordinary Layout good.
	app.dispatch({"type": "set_mode", "mode": "edit"})
	app._refresh()
	await settle(0.4)
	await capture("09-edit-layout")
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": manifest}, "\t"))
	file.close()
	print("Captured %d #61 screens" % manifest.size())
	app.queue_free()
	await process_frame
	quit(0)

## Real frames pass: the game's own _process advances the view clock, flights
## and the counter (service stays paused in this capture).
func settle(seconds: float) -> void:
	await create_timer(seconds).timeout
	app._refresh()

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(destination.path_join(name + ".png"))
	manifest.append({"name": name, "pixels": [image.get_width(), image.get_height()], "coins": app.session.snapshot().coins, "tips": app.session.snapshot().tips})
