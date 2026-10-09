extends SceneTree

const Model = preload("res://scripts/restaurant_model.gd")
var failures := 0
var checks := 0

func _init() -> void:
	_test_starter_service()
	_test_local_backpressure()
	_test_full_loop()
	_test_chef_recipe_and_tiers()
	_test_edit_preservation()
	_test_inventory_economy()
	_test_reachable_seats_and_rescue()
	_test_save_roundtrip()
	_test_offline_layout()
	print("Restaurant tests: %d checks, %d failures" % [checks, failures])
	quit(1 if failures or checks < 40 else 0)

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(label)

func blank() -> RefCounted:
	var m := Model.new()
	m.data.objects.clear()
	m.data.customers.clear()
	m.data.expanded = true
	return m

func _test_starter_service() -> void:
	var m := Model.new()
	var before := float(m.data.coins)
	var events: Array = m.tick(75.0)
	check(m.data.stats.sales >= 8,"Starter restaurant sells autonomously")
	check(float(m.data.coins) > before,"Dish consumption credits coins")
	check(m.data.stats.visitors >= 6,"Customers enter and find seats")
	check(m.data.stats.served > 0,"Visits complete with varying hidden appetite")
	check(events.any(func(e): return e.type == "sale"),"Sale feedback events emitted")
	check(m.data.objects.filter(func(o): return o.kind == "chef").size() == 1,"Starter has one chef")
	for person in m.data.customers:
		check(not person.has("fullness_bar"),"No customer fullness UI state")

func _test_local_backpressure() -> void:
	var m := blank()
	var a: Dictionary = m._add_object("belt",1,1,1)
	var b: Dictionary = m._add_object("belt",2,1,1)
	var c: Dictionary = m._add_object("belt",3,1,1)
	var d: Dictionary = m._add_object("belt",1,3,1)
	var e: Dictionary = m._add_object("belt",2,3,1)
	a.dish = "cucumber"
	b.dish = "salmon"
	c.dish = "shrimp"
	d.dish = "eel"
	m._move_belts()
	check(a.dish == "cucumber" and b.dish == "salmon" and c.dish == "shrimp","Open endpoint queues dishes without deletion")
	check(d.dish == "" and e.dish == "eel","Backpressure remains local to blocked path")
	c.dish = ""
	m._move_belts()
	check(a.dish == "" and b.dish == "cucumber" and c.dish == "salmon","Removing a dish advances upstream plates together")

func _test_full_loop() -> void:
	var m := blank()
	var a: Dictionary = m._add_object("belt",1,1,1)
	var b: Dictionary = m._add_object("belt",2,1,2)
	var c: Dictionary = m._add_object("belt",2,2,3)
	var d: Dictionary = m._add_object("belt",1,2,0)
	a.dish = "cucumber"
	b.dish = "salmon"
	c.dish = "shrimp"
	d.dish = "eel"
	m._move_belts()
	check(a.dish == "eel" and b.dish == "cucumber" and c.dish == "salmon" and d.dish == "shrimp","Full loop circulates every dish simultaneously")
	var extra: Dictionary = m._add_object("belt",3,1,3)
	check(m.connect_belt(extra.id,b.id),"Path builder connects neighboring belt")
	check(int(a.dir) == -1,"Path reorientation removes prior incoming connection")
	check(not m.connect_belt(extra.id,d.id),"Non-neighboring belt connection rejected")

func _test_chef_recipe_and_tiers() -> void:
	var m := Model.new()
	var chef: Dictionary = m.data.objects.filter(func(o): return o.kind == "chef")[0]
	check(not m.assign_recipe(chef.id,"salmon"),"Undiscovered recipe cannot be assigned")
	m.data.recipes.append("salmon")
	chef.progress = 0.5
	chef.dish = "cucumber"
	check(m.assign_recipe(chef.id,"salmon"),"Discovered Wood recipe assignable at level 1")
	check(chef.progress == 0.0 and chef.dish == "","Changing recipe resets work and held plate")
	m.data.recipes.append("shrimp")
	check(not m.assign_recipe(chef.id,"shrimp"),"Higher-tier recipe requires chef level")
	m.data.coins = 1000.0
	var old_time: float = m.chef_prep_time(chef)
	m.upgrade_chef(chef.id)
	m.upgrade_chef(chef.id)
	check(m.assign_recipe(chef.id,"shrimp"),"Level 3 unlocks Steel recipe")
	check(m.chef_prep_time(chef,"salmon") < old_time,"Level-up improves cooking speed")
	chef.dir = 3
	m.tick(20.0)
	check(chef.dish == "shrimp" and chef.progress == 1.0,"Disconnected chef holds exactly one prepared dish")

func _test_edit_preservation() -> void:
	var m := Model.new()
	m.tick(14.0)
	var occupied: Array = m.data.objects.filter(func(o): return o.kind == "seat" and not o.customer.is_empty())
	check(not occupied.is_empty(),"Simulation provides occupied seat for editing")
	if occupied.is_empty():
		return
	var seat: Dictionary = occupied[0]
	var person: Dictionary = seat.customer
	var meal: int = person.eaten
	check(m.move_object(seat.id,4,7),"Occupied seat can move into empty floor")
	check(person.x == 4 and person.y == 7 and person.eaten == meal,"Moving seat carries customer and meal progress")
	check(m.remove_object(seat.id),"Occupied seat can be removed")
	check(person.state == "searching" and person.eaten == meal,"Removed seat customer retains meal and searches")
	var chef: Dictionary = m.data.objects.filter(func(o): return o.kind == "chef")[0]
	chef.level = 4
	var id: int = chef.id
	m.remove_object(id)
	check(m.place("chef",4,6),"Unassigned chef can be placed again")
	check(m.get_object(id).level == 4,"Unassignment preserves chef identity and level")
	var belt: Dictionary = m.object_at(3,2)
	belt.dish = "salmon"
	m.move_object(belt.id,1,6)
	check(belt.dish == "salmon","Moving belt carries its plate")
	var coins: float = m.data.coins
	m.remove_object(belt.id)
	check(m.data.coins == coins,"Removing belt discards plate without income")

func _test_inventory_economy() -> void:
	var m := Model.new()
	var before: int = m.data.inventory.belt
	var cash: float = m.data.coins
	check(m.buy("belt"),"Affordable belt can be bought")
	check(m.data.inventory.belt == before + 1,"Purchase goes to inventory")
	check(m.data.coins == cash - m.price_for("belt"),"Purchase pays exact displayed price")
	check(m.place("belt",1,6),"Inventory item places on empty cleared floor")
	check(not m.place("belt",1,6),"Cannot place two objects on same cell")
	check(not m.place("belt",0,0),"Uncleared expansion cells reject placement")
	m.data.coins = 1000.0
	check(m.expand() and m.is_floor(0,0),"Expansion permanently clears border floor")
	check(not m.expand(),"Already-cleared expansion cannot be charged again")
	m.data.coins = 0.0
	check(not m.buy("chef"),"Unaffordable hiring disabled")

func _test_reachable_seats_and_rescue() -> void:
	var m := blank()
	var seat: Dictionary = m._add_object("seat",3,3,0)
	for position in [[3,2],[4,3],[3,4],[2,3]]:
		m._add_object("belt",position[0],position[1],0)
	m._spawn_customer()
	check(m.data.customers.is_empty(),"Unreachable seat does not teleport customer through objects")
	var open_seat: Dictionary = m._add_object("seat",5,6,0)
	m._spawn_customer()
	check(m.data.customers.size() == 1,"Reachable seat admits customer")
	var person: Dictionary = m.data.customers[0]
	check(int(person.seat_id) == int(open_seat.id),"Customer reserves reachable seat")
	check(m.move_customer(person.id,3,3),"Player can rescue or seat customer by dragging across unreachable floor")
	check(person.state == "seated" and seat.customer.id == person.id,"Dropping on free seat preserves customer visit")

func _test_save_roundtrip() -> void:
	var original := Model.new()
	original.tick(17.3)
	var loaded := Model.new()
	var saved: Dictionary = JSON.parse_string(JSON.stringify(original.serialize()))
	loaded.restore(saved)
	original.tick(30.0)
	loaded.tick(30.0)
	check(original.data.coins == loaded.data.coins,"Save/reload preserves exact simulation earnings")
	check(original.data.stats == loaded.data.stats,"Save/reload preserves seeded customer outcomes")
	check(original.data.customers.size() == loaded.data.customers.size(),"Save/reload preserves customer lifecycle")
	for seat in loaded.data.objects:
		if seat.kind == "seat" and not seat.customer.is_empty():
			check(loaded.data.customers.has(seat.customer),"Restore reconnects occupied seat to customer")

func _test_offline_layout() -> void:
	var m := Model.new()
	var before: float = m.data.coins
	var reward: int = m.offline_income(3600.0)
	check(reward > 0 and m.data.coins == before + reward,"Offline earnings credit the current functioning layout")
	var broken := Model.new()
	for obj in broken.data.objects:
		if obj.kind == "chef":
			obj.dir = 3
		if obj.kind == "belt":
			obj.dish = ""
	check(broken.offline_income(3600.0) == 0,"Disconnected restaurant earns no generic offline allowance")
	var long_absence := Model.new()
	check(long_absence.offline_income(86400.0 * 3) > reward * 60,"Offline income accumulates without a time cap")
