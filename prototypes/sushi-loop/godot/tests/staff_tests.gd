extends SceneTree
const Session = preload("res://scripts/session.gd")
var count := 0
var failures: Array[String] = []
func check(ok: bool, message: String) -> void:
	count += 1
	if not ok: failures.append(message)
func _initialize() -> void:
	var session = Session.new_session(81,{"starting_coins":1000})
	check(not session.command({"type":"staff_place","inventory_id":"belt-tile","x":0,"y":5}).ok,"Live placement only accepts unassigned chefs")
	check(session.snapshot().staff.count==3,"starter roster retained")
	var offers: Array = session.snapshot().staff.offers
	check(offers.size()==3,"three persistent offers")
	var rng: String = session.save_data().random_state
	var first: Dictionary = offers[0]
	var hired: Dictionary = session.command({"type":"hire_applicant","offer_id":first.id})
	check(hired.ok,"hire succeeds")
	check(session.snapshot().coins==820,"exact debit")
	check(session.snapshot().staff.count==4 and session.snapshot().staff.offers.size()==2,"pool not refilled")
	var stock: Dictionary = session.snapshot().inventory.filter(func(item): return item.id==hired.chef_id)[0]
	check(not stock.assigned and stock.staff_new and stock.recipe_id=="","new chef unassigned, unread and idle")
	check(not session.command({"type":"hire_applicant","offer_id":first.id}).ok,"offer consumed once")
	check(session.command({"type":"hire_applicant","offer_id":offers[1].id}).reason=="staff_full","capacity counts stored and assigned")
	var saved: Dictionary = JSON.parse_string(JSON.stringify(session.save_data()))
	var restored = Session.new()
	check(restored.restore(saved),"round trip includes hired roster")
	check(JSON.parse_string(JSON.stringify(restored.snapshot().staff))==JSON.parse_string(JSON.stringify(session.snapshot().staff)),"pool and receipt survive reopening")
	check(restored.command({"type":"refresh_applicants","now":1000.0}).ok,"explicit free refresh")
	check(restored.snapshot().staff.offers.size()==3 and restored.snapshot().coins==820,"refresh replaces three without payment")
	check(restored.save_data().random_state==rng,"refresh independent of service RNG")
	var pool: Array = restored.snapshot().staff.offers
	check(restored.command({"type":"refresh_applicants","now":1299.0}).reason=="refresh_cooldown","real-time deadline enforced")
	check(restored.snapshot().staff.offers==pool,"cooldown does not replace offers")
	check(restored.command({"type":"refresh_applicants","now":1300.0}).ok,"deadline expires explicitly")
	check(restored.command({"type":"staff_seen","ids":[hired.chef_id]}).ok,"seen acknowledgement")
	var before: Dictionary = session.save_data()
	check(not session.command({"type":"staff_place","inventory_id":hired.chef_id,"x":1,"y":6}).ok,"occupied drop rejected")
	check(session.save_data()==before,"invalid drop atomic")
	var placed := session.command({"type":"staff_place","inventory_id":hired.chef_id,"x":1,"y":5})
	check(placed.ok,"live placement beside belt")
	check(session.snapshot().mode=="live" and session.snapshot().camera==before.state.camera,"live mode/camera preserved")
	var actor: Dictionary = session.snapshot().objects.filter(func(item): return item.id==hired.chef_id)[0]
	check(actor.recipe_id=="" and not actor.active,"closing picker leaves idle")
	check(session.command({"type":"prepare_recipe","chef_id":hired.chef_id,"recipe_id":"salmon_nigiri"}).ok,"explicit Prepare")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(session.save_data()))),"assignment and payment restore")
	var legacy: Dictionary = Session.new_session(1).save_data();legacy.erase("staff_version");legacy.state.erase("staff")
	for item in legacy.state.inventory: item.erase("staff_new")
	check(Session.new().restore(legacy),"legacy save migrates without reset")
	var poor = Session.new_session(2,{"starting_coins":0})
	var unchanged: Dictionary = poor.save_data()
	check(poor.command({"type":"hire_applicant","offer_id":poor.snapshot().staff.offers[0].id}).reason=="not_enough_coins","unaffordable hire fails")
	check(poor.save_data()==unchanged,"unaffordable hire atomic")
	for failure in failures: printerr("FAIL: "+failure)
	print("%s: %s staff checks" % ["PASS" if failures.is_empty() else "FAIL",count])
	quit(0 if failures.is_empty() else 1)
