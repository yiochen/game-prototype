extends SceneTree
## Tea (#62): cup geometry -> fill, tilt -> flow, the one-pour ending and
## grading (features/tea.gd), and the session's request rules: between dishes,
## after other bubbles, no sushi while waiting, an open pour that never expires,
## cancel, finish once, the tip bonus and saves.
const Session = preload("res://scripts/session.gd")
const Tips = preload("res://scripts/features/tips.gd")
const Tea = preload("res://scripts/features/tea.gd")
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func rise_seconds(c: Dictionary, from: float, to: float) -> float:
	return (Tea.volume_at(c, to) - Tea.volume_at(c, from)) / 1000.0

func roundtrip(s):
	var copy = Session.new()
	return copy if copy.restore(JSON.parse_string(JSON.stringify(s.save_data()))) else null

func guest(s, id: String) -> Dictionary:
	for customer in s.snapshot().customers:
		if customer.id == id: return customer
	return {}

## Advances until some guest asks for tea; returns that guest's id.
func next_request(s, limit := 2400) -> String:
	for step in range(limit):
		for event in s.advance(0.25):
			if event.type == "tea_requested": return str(event.customer_id)
	return ""

func run() -> void:
	# ---- geometry and pouring rules
	var hourglass := Tea.cup("hourglass")
	check(rise_seconds(hourglass, 10, 24) > rise_seconds(hourglass, 70, 83) * 5.0, "the same flow climbs the narrow waist far faster than the wide body")
	var bowl := Tea.cup("bowl")
	check(rise_seconds(bowl, 80, 90) > rise_seconds(bowl, 0, 10) * 5.0, "a bowl fills fast at its narrow foot and slowly near the wide rim")
	var inverse := true
	for id in Tea.cup_ids():
		var c := Tea.cup(id)
		for y in [0.0, 7.3, float(c.height) * 0.5, float(c.target_height), float(c.height)]:
			if absf(Tea.level_for(c, Tea.volume_at(c, y)) - y) > 0.05: inverse = false
	check(inverse, "level and volume invert each other for every cup")
	var vase := Tea.cup("vase")
	var unshifted := 0.0
	for index in range(1, vase.radii.size()): unshifted += PI * pow((vase.radii[index - 1] + vase.radii[index]) * 0.5, 2.0) * Tea.STEP
	check(absf(unshifted - float(vase.capacity)) < 0.001 and absf(Tea.shift_at(vase, 150)) > 5.0, "the crooked offset adds no capacity")
	check(Tea.flow_share(0.0) == 0.0 and Tea.flow_share(0.12) == 0.0 and Tea.flow_share(0.5) < Tea.flow_share(0.8) and Tea.flow_share(1.0) == 1.0, "upright pours nothing and more tilt pours more")
	for id in Tea.cup_ids():
		var pour := Tea.new_pour(id)
		var seconds := 0.0
		while float(pour.volume) < float(Tea.cup(id).target_volume):
			Tea.step(pour, 1.0 / 60.0, 1.0, true)
			seconds += 1.0 / 60.0
		check(absf(seconds - 2.2) < 0.05, "%s reaches its line in about 2.2 s at full tilt (%.2f)" % [id, seconds])
	var drips: Array = []
	for setup in [[0.4, 0.5], [0.8, 1.0]]:
		var pour := Tea.new_pour("yunomi")
		for frame in range(int(setup[0] * 60)): Tea.step(pour, 1.0 / 60.0, setup[1], true)
		var before := float(pour.volume)
		for frame in range(60): Tea.step(pour, 1.0 / 60.0, 0.0, false)
		drips.append(float(pour.volume) - before)
	check(absf(drips[0] - drips[1]) < 0.000001, "the trailing drops are the same whatever the flow was")
	var single := Tea.new_pour("bowl")
	Tea.step(single, 1.0 / 60.0, 0.05, true)
	check(not Tea.done(single), "lifting inside the dead zone is not a pour")
	for frame in range(30): Tea.step(single, 1.0 / 60.0, 0.7, true)
	Tea.step(single, 1.0 / 60.0, 0.05, true)
	check(not Tea.done(single), "easing back ends the flow, but the drops are still falling")
	for frame in range(60): Tea.step(single, 1.0 / 60.0, 0.0, false)
	check(Tea.done(single), "one pour: easing back or letting go serves once the drops land")
	var flask := Tea.new_pour("flask")
	flask.volume = float(Tea.cup("flask").target_volume)
	check(Tea.grade(flask).id == "ideal", "a pour on the line is ideal")
	flask.volume = float(Tea.cup("flask").target_volume) * 0.3
	check(Tea.grade(flask).id == "under" and not Tea.grade(flask).qualifies, "a very light pour earns no tea bonus")
	var spill := Tea.new_pour("flask")
	for frame in range(360): Tea.step(spill, 1.0 / 60.0, 1.0, true)
	check(float(spill.spilled) > 0.0 and float(spill.volume) == float(Tea.cup("flask").capacity) and Tea.grade(spill).id == "overflow" and Tea.grade(spill).qualifies, "overflow spills, still counts as served")

	# ---- session rules
	var s = Session.new_session(41)
	var first := next_request(s)
	check(not first.is_empty(), "guests ask for tea during service")
	var asking := guest(s, first)
	check(asking.phase == "waiting" and asking.preference_phase == "complete", "a request starts between dishes, after the guest's other bubbles")
	check(asking.tea_cup in Tea.cup_ids() and asking.tea_progress > 0.9, "the request carries a cup and a full patience rim")
	check(not s.command({"type": "tea_pour_finish", "customer_id": first, "grade": "good", "fill": 1.0}).ok, "a pour must be open to finish")
	# Waiting for tea: no sushi.
	var ate := false
	for step in range(12):
		for event in s.advance(0.25):
			if event.type == "eating_started" and event.get("customer_id") == first: ate = true
	check(not ate and guest(s, first).phase == "waiting", "a guest waiting for tea leaves passing dishes on the belt")
	var progress: float = guest(s, first).tea_progress
	check(s.command({"type": "tea_pour_open", "customer_id": first}).ok and guest(s, first).tea_phase == "pouring", "tapping the bubble opens the pour and dismisses the bubble")
	var others := {}
	for step in range(240):
		for event in s.advance(0.25):
			if event.get("customer_id") != first and event.type in ["tea_requested", "tea_missed"]: others[event.type] = int(others.get(event.type, 0)) + 1
			if event.type == "eating_started" and event.get("customer_id") == first: ate = true
	check(guest(s, first).tea_phase == "pouring" and not ate, "an open pour never expires and the guest keeps waiting (60 s)")
	check(int(others.get("tea_missed", 0)) > 0, "other requests keep their own clocks and can lapse during a pour (%s)" % [others])
	var waiting: Array = s.snapshot().customers.filter(func(c): return c.tea_phase == "requested")
	if not waiting.is_empty():
		check(not s.command({"type": "tea_pour_open", "customer_id": waiting[0].id}).ok, "only one pour is open at a time")
	var reopened = roundtrip(s)
	check(reopened != null and guest(reopened, first).tea_phase == "requested", "a guest saved mid-pour is asking again after reopening")
	check(s.command({"type": "tea_pour_cancel", "customer_id": first}).ok and is_equal_approx(guest(s, first).tea_progress, progress), "closing before pouring brings the bubble back with the same patience")
	var missed := false
	for step in range(60):
		for event in s.advance(0.25):
			if event.type == "tea_missed" and event.get("customer_id") == first: missed = true
	check(missed and guest(s, first).tea_phase == "missed", "an unanswered request lapses")
	ate = false
	for step in range(240):
		for event in s.advance(0.25):
			if event.type == "eating_started" and event.get("customer_id") == first: ate = true
		if ate or guest(s, first).is_empty(): break
	check(ate or guest(s, first).is_empty() or guest(s, first).phase == "leaving", "after a lapse the guest eats again")

	var served := next_request(s)
	check(s.command({"type": "tea_pour_open", "customer_id": served}).ok, "a second guest's pour opens")
	var finished: Dictionary = s.command({"type": "tea_pour_finish", "customer_id": served, "grade": "ideal", "fill": 1.0})
	check(finished.ok and finished.qualifies and guest(s, served).tea_phase == "served", "finishing serves the tea")
	var row: Dictionary = s._customer_by_id(served)
	check(is_equal_approx(Tips.chance(row), 0.5 if row.request_eaten else 0.25), "an ideal pour raises the tip chance to 25% (the eaten request's 50% still wins), never to certainty")
	check(not s.command({"type": "tea_pour_finish", "customer_id": served, "grade": "ideal", "fill": 1.0}).ok and not s.command({"type": "tea_pour_open", "customer_id": served}).ok, "a serving completes once")
	check(not s.command({"type": "tea_pour_finish", "customer_id": "x", "grade": "great", "fill": 1.0}).ok, "unknown guests and grades are refused")
	var copy = roundtrip(s)
	check(copy != null and guest(copy, served).tea_phase == "served", "served tea survives a save")

	# Across a long service, every request waits for the guest's other bubbles.
	var service = Session.new_session(7)
	var clean := true
	var asked := 0
	for step in range(2400):
		for event in service.advance(0.25):
			if event.type != "tea_requested": continue
			asked += 1
			var c := guest(service, str(event.customer_id))
			if c.preference_phase != "complete" or c.phase != "waiting": clean = false
	check(asked > 0 and clean, "no tea bubble ever shares a guest with another bubble (%d requests)" % asked)
	print("Tea: %d checks, %d failures" % [count, failures.size()])
	quit(1 if not failures.is_empty() else 0)
