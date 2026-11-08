extends SceneTree
## Tips (#61): tip decision, floor drops, jar routing, collection, upgrades,
## layout sweeps and saves. Runs headless through the public command boundary,
## plus the session's tip decision for exact routing cases.
const Session = preload("res://scripts/session.gd")
const Tips = preload("res://scripts/features/tips.gd")
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func seat_of(s) -> Dictionary:
	return s.snapshot().objects.filter(func(o): return o.kind == "seat")[0]

func guest(s, seat: Dictionary, bill: int, extra := {}) -> Dictionary:
	var customer := {"id": "customer-test-%d" % count, "seat_id": seat.id, "x": float(seat.x), "y": float(seat.y), "phase": "leaving"}
	customer.merge(Tips.VISIT_FIELDS.duplicate(true), true)
	customer.bill = bill
	customer.merge(extra, true)
	return customer

func decide(s, customer: Dictionary) -> Dictionary:
	s._pending_events.clear()
	s._decide_tip(customer)
	var events: Array = s._pending_events.duplicate(true)
	s._pending_events.clear()
	return events[0] if not events.is_empty() else {}

func buy_and_place_jar(s, x: int, y: int) -> bool:
	s.command({"type": "set_mode", "mode": "edit"})
	var bought: bool = s.command({"type": "shop_purchase", "offer_id": "tip-jar", "expected_sequence": s.snapshot().shop.purchase_sequence}).get("ok", false)
	var placed: bool = s.command({"type": "editor_place", "inventory_id": "tip-jar", "x": x, "y": y}).get("ok", false)
	s.command({"type": "set_mode", "mode": "live"})
	return bought and placed

func fill_around(s, center: Vector2i) -> void:
	for cell in Tips.around(center):
		if s._cash_cell_open(cell): s._state.tips.cash.append({"x": cell.x, "y": cell.y, "amount": 1})

func roundtrip(s):
	var copy = Session.new()
	return copy if copy.restore(JSON.parse_string(JSON.stringify(s.save_data()))) else null

func run() -> void:
	# Balance rules.
	check(is_equal_approx(Tips.chance({}), 0.1), "a normal visit tips 10% of the time")
	check(is_equal_approx(Tips.chance({"tea_phase": "served"}), 0.4), "tea adds 30 percentage points once")
	check(is_equal_approx(Tips.chance({"tea_phase": "served", "request_eaten": true}), 1.0) and is_equal_approx(Tips.chance({"request_eaten": true}), 1.0), "an eaten requested dish guarantees a tip")
	check(Tips.amount(48) == 5 and Tips.amount(14) == 1 and Tips.amount(3) == 1 and Tips.amount(250) == 25, "tip is 10% of the bill, rounded, at least 1")
	check(Tips.tier(10) == 0 and Tips.tier(11) == 1 and Tips.tier(50) == 1 and Tips.tier(51) == 2, "piles: one note to $10, three notes to $50, a bundle above")
	check(Tips.capacity(0) < Tips.capacity(1) and Tips.capacity(1) < Tips.capacity(2), "upgrades raise jar capacity")

	var s = Session.new_session(41, {"starting_coins": 5000})
	var seat := seat_of(s)
	var center := Vector2i(int(seat.x), int(seat.y))
	var coins: int = s.snapshot().coins

	# Eligibility and once-only decisions.
	var unpaid := guest(s, seat, 0, {"request_eaten": false})
	check(decide(s, unpaid).is_empty() and not unpaid.tip_evaluated, "a guest who bought nothing never tips")
	var paid := guest(s, seat, 48, {"request_eaten": true})
	var first := decide(s, paid)
	check(first.get("destination") == "floor" and first.amount == 5 and paid.tip_evaluated, "an eaten request tips 10% of the bill onto the floor")
	check(Tips.around(center).has(Vector2i(int(first.x), int(first.y))), "the pile lands on one of the eight tiles around the seat")
	check(decide(s, paid).is_empty() and s.snapshot().tips.cash.size() == 1, "a visit is evaluated once")
	check(s.snapshot().coins == coins, "a floor drop does not touch the wallet")

	# No open tile: the jar is the fallback, only when placed.
	fill_around(s, center)
	var piles: int = s.snapshot().tips.cash.size()
	check(decide(s, guest(s, seat, 48, {"request_eaten": true})).get("destination") == "lost" and s.snapshot().tips.cash.size() == piles, "no tile and no jar: the tip is not kept")
	check(buy_and_place_jar(s, 0, 12), "the tip jar is bought and placed")
	coins = s.snapshot().coins
	var deposit := decide(s, guest(s, seat, 48, {"request_eaten": true}))
	check(deposit.get("destination") == "jar" and deposit.accepted == 5 and s.snapshot().tips.jar.balance == 5, "no tile: the whole tip goes to the placed jar")
	check(s.snapshot().coins == coins, "a jar deposit does not raise the wallet")
	s._state.tips.jar.balance = Tips.capacity(0) - 2
	var partial := decide(s, guest(s, seat, 48, {"request_eaten": true}))
	check(partial.get("destination") == "jar" and partial.accepted == 2 and partial.full and s.snapshot().tips.jar.balance == Tips.capacity(0), "a nearly full jar keeps only what fits")
	check(decide(s, guest(s, seat, 48, {"request_eaten": true})).get("destination") == "lost", "a full jar keeps nothing")

	# Collection credits once.
	coins = s.snapshot().coins
	var jar_value: int = s.snapshot().tips.jar.balance
	var collected: Dictionary = s.command({"type": "collect_jar"})
	check(collected.ok and collected.amount == jar_value and s.snapshot().coins == coins + jar_value and s.snapshot().tips.jar.balance == 0, "tapping the jar moves its whole balance to the wallet")
	check(not s.command({"type": "collect_jar"}).ok and s.snapshot().coins == coins + jar_value, "an empty jar credits nothing more")
	coins = s.snapshot().coins
	var pile: Dictionary = s.snapshot().tips.cash[0]
	var expected := 0
	for other in s.snapshot().tips.cash:
		if absi(int(other.x) - int(pile.x)) <= 1 and absi(int(other.y) - int(pile.y)) <= 1: expected += int(other.amount)
	var taken: Dictionary = s.command({"type": "collect_cash", "x": pile.x, "y": pile.y})
	check(taken.ok and taken.amount == expected and s.snapshot().coins == coins + expected, "a tap collects the pile and its neighbours within one tile")
	check(not s.command({"type": "collect_cash", "x": pile.x, "y": pile.y}).ok and s.snapshot().coins == coins + expected, "collected cash cannot be collected twice")
	check(not s.command({"type": "collect_cash", "x": 0, "y": 0}).ok, "an empty tile collects nothing")

	# Layout edits collect covered cash first.
	var spot: Vector2i = Vector2i(-1, -1)
	for y in range(4, 12):
		for x in range(0, 6):
			if spot.x < 0 and s._cash_cell_open(Vector2i(x, y)): spot = Vector2i(x, y)
	s._state.tips.cash.append({"x": spot.x, "y": spot.y, "amount": 7})
	coins = s.snapshot().coins
	s.command({"type": "set_mode", "mode": "edit"})
	var placed: Dictionary = s.command({"type": "editor_place", "inventory_id": "plant-angular", "x": spot.x, "y": spot.y})
	check(placed.ok and placed.get("cash_collected", []).size() == 1 and s.snapshot().coins == coins + 7, "placing furniture on cash collects it first")
	check(s.snapshot().tips.cash.all(func(p): return Vector2i(int(p.x), int(p.y)) != spot), "no pile remains under furniture")

	# Moving and storing the jar keeps its money and level.
	s._state.tips.jar.balance = 40
	check(s.command({"type": "tip_jar_upgrade", "expected_level": 0}).ok and s.snapshot().tips.jar.level == 1 and s.snapshot().tips.jar.capacity == Tips.capacity(1), "an upgrade raises capacity")
	check(not s.command({"type": "tip_jar_upgrade", "expected_level": 0}).ok, "a replayed upgrade is rejected")
	var jar_id: String = s.snapshot().tips.jar.id
	check(s.command({"type": "editor_remove", "id": jar_id}).ok and not s.snapshot().tips.jar.placed and s.snapshot().tips.jar.balance == 40, "storing the jar keeps its balance")
	s.command({"type": "set_mode", "mode": "live"})
	fill_around(s, center)
	check(decide(s, guest(s, seat, 48, {"request_eaten": true})).get("destination") == "lost" and s.snapshot().tips.jar.balance == 40, "an unplaced jar receives nothing")
	s.command({"type": "set_mode", "mode": "edit"})
	check(s.command({"type": "editor_place", "inventory_id": "tip-jar", "x": 0, "y": 12}).ok and s.snapshot().tips.jar.balance == 40 and s.snapshot().tips.jar.level == 1, "placing it again keeps balance and level")
	s.command({"type": "set_mode", "mode": "live"})

	# Tea.
	check(not s.command({"type": "serve_tea", "customer_id": "nobody"}).ok, "tea needs a request")
	# Saves.
	var copy = roundtrip(s)
	check(copy != null, "tips survive a JSON save and reopen")
	if copy != null:
		check(JSON.stringify(copy.snapshot().tips) == JSON.stringify(s.snapshot().tips), "piles, jar balance and level are restored exactly")
		var before: int = copy.snapshot().coins
		var again: Dictionary = copy.command({"type": "collect_jar"})
		check(again.ok and copy.snapshot().coins == before + 40, "reopened jar money is collected once")

	# A save from before tips loads with an empty slice and the jar in stock.
	var old: Dictionary = Session.new_session(9).save_data()
	old.engine.slices.erase("tips")
	old.engine.slices.shop.version = 1
	old.engine.slices.shop.data.stock.erase("tip-jar")
	old.engine.slices.shop.data.purchased.erase("tip-jar")
	old.engine.slices.inventory.version = 1
	old.engine.slices.inventory.data = old.engine.slices.inventory.data.filter(func(e): return e.id != "tip-jar")
	var upgraded = Session.new()
	check(upgraded.restore(JSON.parse_string(JSON.stringify(old))), "a save from before tips still opens")
	if upgraded.get("_state").has("tips"):
		check(upgraded.snapshot().tips.cash.is_empty() and upgraded.snapshot().shop.offers.any(func(o): return o.id == "tip-jar" and o.remaining == 1), "it gains an empty jar slice and the jar offer")

	# Corrupt tip state is rejected.
	var flat: Dictionary = Session.flat_view(s.save_data())
	flat.state.tips.cash.append({"x": flat.state.tips.cash[0].x if not flat.state.tips.cash.is_empty() else 0, "y": flat.state.tips.cash[0].y if not flat.state.tips.cash.is_empty() else 4, "amount": 0})
	check(not Session.new().restore(flat), "a zero-value or duplicate pile is rejected")

	# Live service: guests tip, ask for tea, and nothing breaks across saves.
	var live = Session.new_session(41)
	var outcomes := {}
	var requested := 0
	for step in range(2400):
		for event in live.advance(0.25):
			if event.type == "tip": outcomes[event.destination] = int(outcomes.get(event.destination, 0)) + 1
			if event.type == "tea_requested":
				requested += 1
				if requested % 2 == 1: live.command({"type": "serve_tea", "customer_id": event.customer_id})
		if step % 400 == 0:
			var reopened = roundtrip(live)
			check(reopened != null, "service save %d reopens" % step)
	check(int(outcomes.get("floor", 0)) > 0, "guests leave floor tips during service (%s)" % [outcomes])
	check(requested > 0, "guests ask for tea during service")
	print("Tips: %d checks, %d failures" % [count, failures.size()])
	quit(1 if not failures.is_empty() else 0)
