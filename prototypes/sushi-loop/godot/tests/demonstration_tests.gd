extends SceneTree
## The shipped exhibition scene must demonstrate #11 through normal service.

const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	var game = Session.new_session(41)
	var start: Dictionary = game.snapshot()
	var chefs: Array = start.objects.filter(func(object): return object.kind == "chef")
	var seats: Array = start.objects.filter(func(object): return object.kind == "seat")
	_expect(start.floor.viewport_columns == 7, "The demonstration keeps the approved seven-column scale")
	_expect(chefs.filter(func(chef): return chef.active).size() == 2 and chefs.any(func(chef): return not chef.active), "Two operating menus and one disconnected chef are observable in the scene")
	_expect(seats.filter(func(seat): return seat.active).size() == 4 and seats.any(func(seat): return not seat.active), "Useful seats contrast with an inactive disconnected seat")
	var menu := {}
	var inactive_seats := {}
	for chef in chefs:
		if chef.active: menu[chef.recipe_id] = true
	for seat in seats:
		if not seat.active: inactive_seats[seat.id] = true
	_expect(menu.size() == 2, "The two counters visibly offer different recipes")
	var events_by_type := {}
	var sales_per_visit := {}
	var sales_ids := {}
	var correct_revenue := int(start.coins)
	var no_inactive_arrivals := true
	var no_duplicate_sales := true
	var passed := false
	var yielded := false
	for step in range(3600):
		for event in game.advance(0.05):
			events_by_type[event.type] = int(events_by_type.get(event.type, 0)) + 1
			if event.type == "arrived":
				no_inactive_arrivals = no_inactive_arrivals and not inactive_seats.has(event.seat_id)
			if event.type == "sale":
				sales_per_visit[event.customer_id] = int(sales_per_visit.get(event.customer_id, 0)) + 1
				correct_revenue += int(start.recipes[event.recipe_id].price)
				no_duplicate_sales = no_duplicate_sales and not sales_ids.has(event.dish_id)
				sales_ids[event.dish_id] = true
		for customer in game.snapshot().customers:
			yielded = yielded or customer.yielding
			passed = passed or absf(float(customer.render_offset_x)) + absf(float(customer.render_offset_y)) > 0.05
	for kind in ["preference_matched", "preference_expired", "customer_restless", "visit_abandoned"]:
		_expect(int(events_by_type.get(kind, 0)) > 0, "Normal timed play demonstrates " + kind)
	_expect(passed and yielded, "The restaurant's ordinary pedestrian encounters exercise passing and yielding")
	_expect(sales_per_visit.values().any(func(count): return count > 1), "At least one visit naturally includes multiple completed dishes")
	_expect(no_inactive_arrivals, "Arrivals choose useful seats rather than the disconnected demonstration seat")
	_expect(no_duplicate_sales and game.snapshot().coins == correct_revenue, "Mixed-menu sales pay each fixed dish price once; abandonment adds no fine or turnover payout")
	if failures.is_empty():
		print("PASS: %s exhibition scene checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)

func _expect(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)
