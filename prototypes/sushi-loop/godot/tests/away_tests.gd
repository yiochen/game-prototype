extends SceneTree
## Time away (#29): a frozen restaurant, one aggregate income estimate per
## interval, a single credit on resume and one Shop rotation per ended run.
## Every scenario goes through the public command/time/save boundary.
const Session = preload("res://scripts/session.gd")
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func reopen(game: GameSession) -> GameSession:
	var copy := Session.new()
	return copy if copy.restore(JSON.parse_string(JSON.stringify(game.save_data()))) else null

func away(game: GameSession) -> Dictionary:
	return GameSession.flat_view(game.save_data()).state.away

func restaurant(game: GameSession) -> Dictionary:
	var view: Dictionary = game.snapshot()
	# Compared as saved JSON: a reopened save carries the same values at JSON precision.
	return JSON.parse_string(JSON.stringify({"customers": view.customers, "objects": view.objects, "mode": view.mode, "camera": view.camera}))

## A row of belts at y=1 with one chef below its start and seats along it.
## `seat_row` 2 puts seats beside the entrance's side of the belt row; 0 puts
## them behind a wall of belts, unreachable from an entrance on row 3.
func fixture(chefs: int, seat_row := 2, entrance := Vector2i(7, 3), service := {}) -> GameSession:
	var objects: Array = []
	for x in range(8): objects.append({"id": "belt-%d" % x, "kind": "belt", "x": x, "y": 1, "facing": "east"})
	for index in chefs:
		objects.append({"id": "chef-%d" % index, "kind": "chef", "name": "Cook", "x": index, "y": 0 if seat_row == 2 else 2, "facing": "south" if seat_row == 2 else "north", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"})
	for x in range(3, 7): objects.append({"id": "seat-%d" % x, "kind": "seat", "x": x, "y": seat_row, "facing": "north" if seat_row == 2 else "south"})
	var settings := {"belt_seconds_per_cell": 1.1}
	settings.merge(service, true)
	return Session.new_session(29, {"floor": {"columns": 8, "rows": 4, "world_columns": 8, "entrance": {"x": entrance.x, "y": entrance.y}}, "objects": objects, "service": settings})

func run() -> void:
	estimates()
	expedition_return()
	plain_reopen()
	mid_expedition()
	shop_rotation()
	print("Time away: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)

func estimates() -> void:
	# The starter restaurant: the estimate tracks real service without simulating it.
	var starter := Session.new_session(3)
	for i in range(240): starter.advance(0.5)
	var before: int = starter.snapshot().coins
	var estimate: int = starter.away_estimate(1200.0)
	for i in range(2400): starter.advance(0.5)
	var actual: int = starter.snapshot().coins - before
	check(estimate > 0 and estimate >= actual * 0.7 and estimate <= actual * 1.15, "starter estimate %d is close to 20 simulated minutes (%d)" % [estimate, actual])
	check(starter.away_estimate(36000.0) >= starter.away_estimate(1200.0) * 29, "no time cap: ten hours earn thirty times twenty minutes")
	check(starter.away_estimate(0.0) == 0, "no time, no income")
	# Layout constraints.
	var productive := fixture(1)
	check(productive.away_estimate(600.0) > 0, "a connected chef with reachable seats earns")
	var hidden := fixture(1, 0)
	check(hidden.away_estimate(600.0) == 0, "seats behind a belt wall are unreachable and earn nothing")
	var disconnected := fixture(1)
	disconnected.command({"type": "set_mode", "mode": "edit"})
	check(disconnected.command({"type": "editor_rotate", "id": "chef-0"}).ok, "turn the chef away from the belt")
	disconnected.command({"type": "set_mode", "mode": "live"})
	check(disconnected.away_estimate(600.0) == 0, "a chef facing away from the belt contributes nothing")
	var closed := fixture(1)
	closed.command({"type": "set_entrance_open", "open": false})
	check(closed.away_estimate(600.0) == 0, "no arrivals, no income")
	# Loading bottleneck: the belt carries one dish per tile-time.
	var two := fixture(2).away_estimate(600.0)
	var five := fixture(5).away_estimate(600.0)
	check(two > productive.away_estimate(600.0), "a second chef adds supply")
	var slow_belt := fixture(5, 2, Vector2i(7, 3), {"belt_seconds_per_cell": 6.0}).away_estimate(600.0)
	check(slow_belt < five and slow_belt <= int(600.0 / 6.0 * 14 * 0.95) + 1, "a slow belt caps five chefs at one dish per tile-time (%d < %d)" % [slow_belt, five])
	# Development: a faster chef raises a supply-limited estimate.
	var developed := Session.new_session(3, {"starting_coins": 100000})
	var base: int = developed.away_estimate(3600.0)
	for level in range(1, 6): developed.command({"type": "level_up_chef", "chef_id": "chef-2", "expected_level": level})
	check(developed.away_estimate(3600.0) > base, "leveling the maki chef raises the estimate (%d > %d)" % [developed.away_estimate(3600.0), base])
	# Permanent expansion: more arrivals help only when arrivals are the limit.
	var quiet := Session.new_session(3, {"starting_coins": 100000, "service": {"arrival_seconds": 40.0}})
	var narrow: int = quiet.away_estimate(3600.0)
	for id in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4"]: quiet.command({"type": "clear_trash", "id": id})
	check(quiet.away_estimate(3600.0) > narrow, "clearing space brings more guests to an arrival-limited room (%d > %d)" % [quiet.away_estimate(3600.0), narrow])
	var busy := Session.new_session(3, {"starting_coins": 100000})
	var supplied: int = busy.away_estimate(3600.0)
	for id in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4"]: busy.command({"type": "clear_trash", "id": id})
	check(busy.away_estimate(3600.0) == supplied, "a kitchen-limited room earns the same after expansion")
	# Saved Edit mode keeps the accepted pause (open product question).
	var editing := Session.new_session(3)
	editing.command({"type": "set_mode", "mode": "edit"})
	check(editing.away_estimate(600.0) == 0, "saved Edit mode estimates no income")

func expedition_return() -> void:
	var game := Session.new_session(4)
	for i in range(60): game.advance(0.5)
	var frozen := restaurant(game)
	var coins: int = game.snapshot().coins
	var expected: int = game.away_estimate(900.0)
	check(game.command({"type": "expedition_start", "now": 1000.0, "seed": 7}).ok, "expedition starts")
	check(away(game).started == 1000.0, "Start opens the time-away interval")
	check(game.advance(30.0).is_empty() and restaurant(game) == frozen, "the restaurant does not simulate during the dive")
	game.command({"type": "expedition_pause"})
	check(not game.command({"type": "away_resume", "now": 1500.0}).ok, "no credit while the run is still on screen")
	var ended: Dictionary = game.command({"type": "expedition_give_up", "now": 1500.0})
	check(ended.ok and game.advance(10.0).is_empty(), "results and award keep the restaurant frozen")
	check(not game.command({"type": "away_resume", "now": 1600.0}).ok, "no credit before the results are acknowledged")
	game.command({"type": "expedition_acknowledge", "id": ended.result.id})
	var credit: Dictionary = game.command({"type": "away_resume", "now": 1900.0})
	check(credit.ok and credit.amount == expected and credit.amount > 0, "return credits the whole interval once (%s, expected %d)" % [credit.get("amount"), expected])
	check(game.snapshot().coins == coins + expected, "credit lands in the balance")
	check(restaurant(game) == frozen, "guests, dishes and belts are exactly as they were at Start")
	var again: Dictionary = game.command({"type": "away_resume", "now": 1900.0})
	check(again.ok and not again.changed and game.snapshot().coins == coins + expected, "a repeated return never credits again")
	var events: Array = []
	for i in range(20): events.append_array(game.advance(0.5))
	check(not events.is_empty(), "service resumes after the credit")

func plain_reopen() -> void:
	var game := Session.new_session(5)
	for i in range(60): game.advance(0.5)
	check(game.command({"type": "away_begin", "now": 110.0}).changed, "closing opens an interval")
	var expected: int = game.away_estimate(290.0)
	var reopened := reopen(game)
	var frozen := restaurant(reopened)
	check(reopened != null and reopened.advance(5.0).is_empty(), "a reopened, unresumed restaurant stays frozen")
	var coins: int = reopened.snapshot().coins
	var credit: Dictionary = reopened.command({"type": "away_resume", "now": 400.0})
	check(credit.ok and credit.amount == expected and credit.seconds == 290.0, "reopen credits closed time once")
	check(restaurant(reopened) == frozen, "reopen restores the saved restaurant without fast-forwarding")
	var twice := reopen(reopened)
	var repeat: Dictionary = twice.command({"type": "away_resume", "now": 400.0})
	check(repeat.amount == 0 and twice.snapshot().coins == coins + expected, "reopening the credited save again pays nothing")
	var restored := reopen(reopened)
	var running: Dictionary = restored.save_data()
	check(restored.command({"type": "away_resume", "now": 520.0}).amount == 0 and restored.save_data() == running, "returning from dive prep never credits the running restaurant")
	restored.command({"type": "away_begin", "now": 520.0})
	check(restored.command({"type": "away_resume", "now": 520.0}).amount == 0 and restored.save_data() == running, "a zero-length absence leaves the save exactly as it was")
	restored.command({"type": "away_begin", "now": 460.0})
	restored.command({"type": "away_resume", "now": 520.0})
	# A clock moved backwards never re-credits an earlier stretch.
	restored.command({"type": "away_begin", "now": 300.0})
	check(away(restored).started == 520.0, "an interval never starts before the last credit")
	var backwards: Dictionary = restored.command({"type": "away_resume", "now": 200.0})
	check(backwards.amount == 0, "an earlier clock credits nothing")
	var edit := Session.new_session(6)
	edit.command({"type": "set_mode", "mode": "edit"})
	edit.command({"type": "away_begin", "now": 0.0})
	check(edit.command({"type": "away_resume", "now": 3600.0}).amount == 0 and edit.snapshot().mode == "edit", "saved Edit mode resumes in Edit with no income")
	var corrupt: Dictionary = GameSession.flat_view(reopened.save_data())
	corrupt.state.away.started = float(corrupt.state.away.credited_through) - 10.0
	check(not Session.new().restore(corrupt), "an interval overlapping a credited one is rejected")

func mid_expedition() -> void:
	var game := Session.new_session(8)
	for i in range(60): game.advance(0.5)
	var frozen := restaurant(game)
	var expected: int = game.away_estimate(700.0)
	game.command({"type": "expedition_start", "now": 1000.0, "seed": 7})
	check(not game.command({"type": "away_begin", "now": 1100.0}).changed, "closing mid-dive keeps the dive's interval")
	var reopened := reopen(game)
	check(reopened.snapshot().expedition.run != null and not reopened.command({"type": "away_resume", "now": 1200.0}).ok, "reopening mid-dive returns to the dive without a credit")
	reopened.command({"type": "expedition_pause"})
	var ended: Dictionary = reopened.command({"type": "expedition_give_up", "now": 1600.0})
	reopened.command({"type": "expedition_acknowledge", "id": ended.result.id})
	var credit: Dictionary = reopened.command({"type": "away_resume", "now": 1700.0})
	check(credit.amount == expected and credit.seconds == 700.0, "dive plus closed time is one interval")
	check(restaurant(reopened) == frozen, "the restaurant from Start is restored after a mid-dive reopen")

func shop_rotation() -> void:
	var game := Session.new_session(9, {"starting_coins": 5000})
	game.command({"type": "set_mode", "mode": "edit"})
	for id in ["plant", "tip-jar"]: game.command({"type": "shop_purchase", "offer_id": id, "expected_sequence": game.snapshot().shop.purchase_sequence})
	var offer := func(id: String) -> Dictionary: return game.snapshot().shop.offers.filter(func(o): return o.id == id)[0]
	check(offer.call("plant").remaining == 1 and offer.call("tip-jar").remaining == 0, "purchases reduce limited stock")
	game.command({"type": "set_mode", "mode": "live"})
	check(not game.snapshot().shop.fresh, "no dot before a rotation")
	var floor_rotation: int = game.snapshot().floor_styles.rotation
	game.command({"type": "expedition_start", "now": 10.0, "seed": 7})
	check(game.snapshot().shop.rotation == 0, "Start does not rotate stock")
	var saved := reopen(game)
	game.command({"type": "expedition_pause"})
	var ended: Dictionary = game.command({"type": "expedition_give_up", "now": 20.0})
	check(game.snapshot().shop.rotation == 1 and game.snapshot().floor_styles.rotation == floor_rotation + 1, "an ended run rotates Shop and floor stock once")
	check(offer.call("plant").remaining == 2 and offer.call("belt").remaining == null, "limited stock restocks; essentials stay unlimited")
	check(offer.call("tip-jar").remaining == 0, "the one tip jar per restaurant does not restock once owned")
	check(game.snapshot().shop.fresh, "new stock shows the dot")
	game.command({"type": "expedition_acknowledge", "id": ended.result.id})
	game.command({"type": "away_resume", "now": 30.0})
	var after := reopen(game)
	after.command({"type": "away_resume", "now": 40.0})
	check(after.snapshot().shop.rotation == 1 and after.snapshot().shop.fresh, "reopen and repeated return never reroll stock")
	check(not game.command({"type": "expedition_give_up", "now": 21.0}).ok and game.snapshot().shop.rotation == 1, "a replayed end cannot rotate again")
	check(game.command({"type": "shop_seen"}).changed and not game.snapshot().shop.fresh, "entering Shop clears the dot")
	check(not game.command({"type": "shop_seen"}).changed, "clearing is idempotent")
	# Ending each run rotates: complete, given up or hull depleted alike.
	saved.command({"type": "expedition_pause"})
	saved.command({"type": "expedition_give_up", "now": 25.0})
	check(saved.snapshot().shop.rotation == 1, "the interrupted copy rotates once on its own end")
	var corrupt: Dictionary = GameSession.flat_view(game.save_data())
	corrupt.state.shop.stock["tip-jar"] = 1
	check(not Session.new().restore(corrupt), "a restocked owned tip jar is rejected")
