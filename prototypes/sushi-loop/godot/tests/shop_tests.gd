extends SceneTree
const Session = preload("res://scripts/session.gd")
var count := 0
var failures: Array[String] = []
func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func buy(session, id: String) -> Dictionary:
	return session.command({"type":"shop_purchase","offer_id":id,"expected_sequence":session.snapshot().shop.purchase_sequence})
func item(session,id: String) -> Dictionary:
	for entry in session.snapshot().inventory:
		if entry.id == id: return entry
	return {}
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var s = Session.new_session(18,{"starting_coins":1240})
	var start: Dictionary = s.save_data()
	check(not buy(s,"belt").ok and s.save_data()==start,"Live rejects Shop purchases atomically")
	s.command({"type":"set_mode","mode":"edit"})
	var stock: int = item(s,"stool-plain").count
	var before: Dictionary = s.save_data()
	var request := {"type":"shop_purchase","offer_id":"stool","expected_sequence":0}
	check(s.command(request).ok,"one affordable purchase")
	check(s.snapshot().coins==1160 and item(s,"stool-plain").count==stock+1,"one debit and one real inventory item")
	var bought: Dictionary = s.save_data()
	check(not s.command(request).ok and s.save_data()==bought,"replayed input cannot duplicate a purchase")
	check(s.advance(20).is_empty() and s.save_data()==bought,"shopping stays paused without elapsed/RNG changes")
	check(s.save_data().random_state==before.random_state,"purchase does not consume restaurant RNG")
	check(s.command({"type":"editor_place","inventory_id":"stool-plain","x":0,"y":5}).ok,"purchased stool uses accepted editor placement")
	var placed: Dictionary = s.snapshot().objects.filter(func(o):return o.get("inventory_id")=="stool-plain")[0]
	check(item(s,"stool-plain").count==stock,"placing consumes one inventory item")
	check(s.command({"type":"editor_remove","id":placed.id}).ok and item(s,"stool-plain").count==stock+1,"Return stores purchased stool without refund")
	check(s.snapshot().coins==1160,"placement/storage never refunds coins")
	for id in ["belt","plant","crate","barrel"]: check(buy(s,id).ok,"buy "+id)
	check(s.snapshot().shop.offers.filter(func(o):return o.id=="barrel")[0].remaining==0,"finite stock decremented to sold out")
	var sold: Dictionary = s.save_data()
	check(not buy(s,"barrel").ok and s.save_data()==sold,"sold out remains unavailable")
	check(s.snapshot().shop.offers.filter(func(o):return o.id=="belt")[0].remaining==null,"unlimited essentials retain unlimited stock")
	var restored = Session.new()
	check(restored.restore(JSON.parse_string(JSON.stringify(sold))),"JSON purchase/stock/inventory save restores")
	check(JSON.parse_string(JSON.stringify(restored.snapshot()))==JSON.parse_string(JSON.stringify(s.snapshot())),"restoring never duplicates inventory or refills stock")
	check(not restored.command(request).ok,"old purchase token rejected after reload")
	check(buy(restored,"belt").ok,"fresh unlimited purchase after reload")
	check(restored.command({"type":"editor_place","inventory_id":"plant-angular","x":0,"y":5}).ok,"bought cosmetic places through editor")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(restored.save_data()))),"placed purchased cosmetic survives reopen")
	var poor = Session.new_session(2,{"starting_coins":24});poor.command({"type":"set_mode","mode":"edit"})
	var poor_before: Dictionary = poor.save_data()
	check(buy(poor,"belt").reason=="not_enough_coins" and poor.save_data()==poor_before,"unaffordable purchase is atomic")
	check(not s.command({"type":"shop_purchase","offer_id":"belt"}).ok,"missing replay token rejected")
	check(not buy(s,"unknown").ok,"unknown offer rejected")
	var legacy: Dictionary = start.duplicate(true);legacy.erase("shop_version");legacy.state.erase("shop")
	var migrated = Session.new();check(migrated.restore(JSON.parse_string(JSON.stringify(legacy))),"0.9.0 save migrates")
	var next: Dictionary = migrated.save_data();next.erase("shop_version");next.state.erase("shop")
	check(JSON.parse_string(JSON.stringify(next))==JSON.parse_string(JSON.stringify(legacy)),"migration retains exact original restaurant/configuration/RNG")
	check(migrated.restore(JSON.parse_string(JSON.stringify(migrated.save_data()))),"migration is repeatable without granting goods")
	for kind in ["stock","purchased","sequence","inventory","future"]:
		var corrupt: Dictionary = sold.duplicate(true)
		match kind:
			"stock": corrupt.state.shop.stock.barrel=1
			"purchased": corrupt.state.shop.purchased["stool-plain"]=-1
			"sequence": corrupt.state.shop.purchase_sequence=0
			"inventory": corrupt.state.inventory.filter(func(e):return e.id=="stool-plain")[0].count+=1
			"future": corrupt.shop_version=99
		var guard: Dictionary = migrated.save_data()
		check(not migrated.restore(corrupt) and migrated.save_data()==guard,"corrupt "+kind+" rejected without mutating session")
	print("Shop rules: %s checks, %s failures" % [count,failures.size()]);quit(0 if failures.is_empty() else 1)
