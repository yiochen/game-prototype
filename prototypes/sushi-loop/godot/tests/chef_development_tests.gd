extends SceneTree
const Session=preload("res://scripts/session.gd")
const Book=preload("res://scripts/recipe_book.gd")
const Development=preload("res://scripts/chef_development.gd")
var count:=0
var failures:Array[String]=[]
func check(value:bool,message:String)->void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func _initialize()->void:call_deferred("run")
func run()->void:
	var session=Session.new_session(81,{"starting_coins":10000})
	var initial:Dictionary=session.save_data()
	var id:String=session.snapshot().objects.filter(func(c):return c.kind=="chef")[0].id
	var actor:=Book.chef(session.save_data().state,id)
	var start:int=actor.level
	var growth:float=actor.growth_rate
	var speed:float=actor.cooking_speed
	var price:=Development.cost(actor)
	check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":start}).ok,"one level purchase")
	actor=Book.chef(session.save_data().state,id)
	check(actor.level==start+1 and absf(actor.cooking_speed-speed-growth)<.000001,"configured growth applies once")
	check(session.snapshot().coins==10000-price,"single debit")
	var bought:Dictionary=session.save_data()
	check(not session.command({"type":"level_up_chef","chef_id":id,"expected_level":start}).ok and session.save_data()==bought,"replayed input is atomic")
	check(not session.command({"type":"level_up_chef","chef_id":id}).ok and session.save_data()==bought,"preview level required")
	check(session.snapshot().recipes==initial.configuration.recipes,"chef development never changes fixed prices/recipes")
	check(session.save_data().random_state==initial.random_state and session.snapshot().elapsed==0,"purchase does not advance clock or RNG")
	while actor.level<3:
		check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"buy tier threshold")
		actor=Book.chef(session.save_data().state,id)
	check(session.command({"type":"discover_recipe","recipe_id":"tamago_nigiri"}).ok and session.command({"type":"prepare_recipe","chef_id":id,"recipe_id":"tamago_nigiri"}).ok,"Yellow unlock grants actual preparation eligibility")
	var time_before:float=session.snapshot().objects.filter(func(c):return c.id==id)[0].preparation_seconds
	session.advance(.5)
	check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"upgrade while preparation underway")
	var active:Dictionary=session.snapshot().objects.filter(func(c):return c.id==id)[0]
	check(active.preparation_seconds<time_before and active.preparation>0,"actual preparation duration improves, fractional work preserved")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(session.save_data()))),"upgraded preparation restores")
	actor=Book.chef(session.save_data().state,id)
	var upgraded:Dictionary=actor.duplicate(true)
	check(session.command({"type":"unassign_chef","chef_id":id}).ok,"unassign works from Live")
	actor=Book.chef(session.save_data().state,id)
	for field in ["level","level_cap","growth_rate","base_cooking_speed","cooking_speed"]:check(actor[field]==upgraded[field],"unassign retains "+field)
	check(not session.command({"type":"prepare_recipe","chef_id":id,"recipe_id":"salmon_nigiri"}).ok,"stored chef cannot prepare")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(session.save_data()))),"stored upgraded chef restores")
	var stored:Dictionary=session.save_data()
	check(not session.command({"type":"staff_place","inventory_id":id,"x":0,"y":3}).ok and session.save_data()==stored,"invalid reassignment is atomic")
	check(session.command({"type":"staff_place","inventory_id":id,"x":1,"y":5}).ok,"valid reassignment uses existing placement")
	actor=Book.chef(session.save_data().state,id)
	check(actor.level==upgraded.level and actor.cooking_speed==upgraded.cooking_speed,"reassignment retains development")
	check(actor.recipe_id=="" and actor.held_dish==null and actor.preparation_elapsed==0,"reassigned chef waits for explicit Prepare")
	while int(actor.level)<int(actor.level_cap):
		check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"development to cap")
		actor=Book.chef(session.save_data().state,id)
	var maximum:Dictionary=session.save_data()
	check(not session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok and session.save_data()==maximum,"MAX cannot exceed cap or debit")
	check(Development.tier(3)=="Yellow" and Development.tier(5)=="Red" and Development.tier(8)=="Blue" and Development.tier(12)=="Black","shared tier thresholds")
	for assigned in [true,false]:
		var firing=Session.new();check(firing.restore(maximum),"restore fire fixture")
		if not assigned:check(firing.command({"type":"unassign_chef","chef_id":id}).ok,"unassigned fire setup")
		var coins:int=firing.snapshot().coins
		check(firing.command({"type":"fire_chef","chef_id":id}).ok and Book.chef(firing.save_data().state,id).is_empty(),"fire removes assigned/stored chef")
		check(firing.snapshot().coins==coins,"fire never refunds")
		var removed:Dictionary=firing.save_data()
		check(not firing.command({"type":"fire_chef","chef_id":id}).ok and firing.save_data()==removed,"repeated Fire cannot remove another chef")
		check(Session.new().restore(JSON.parse_string(JSON.stringify(removed))),"dismissal of starter survives reopening")
	var hire=Session.new_session(7,{"starting_coins":1000})
	var hire_result:Dictionary=hire.command({"type":"hire_applicant","offer_id":hire.snapshot().staff.offers[0].id})
	check(hire_result.ok and hire.command({"type":"fire_chef","chef_id":hire_result.chef_id}).ok,"hired chef can be permanently fired")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(hire.save_data()))),"fired hired mapping restores")
	var legacy:Dictionary=initial.duplicate(true);legacy.erase("chef_development_version");legacy.state.staff.erase("dismissed")
	for c in legacy.state.objects+legacy.state.inventory:
		c.erase("growth_rate");c.erase("base_cooking_speed")
		if c.get("stored_object") is Dictionary:c.stored_object.erase("growth_rate");c.stored_object.erase("base_cooking_speed")
	var migrated=Session.new();check(migrated.restore(legacy),"old shipped save migrates")
	check(migrated.snapshot().coins==initial.state.coins and migrated.save_data().random_state==initial.random_state,"migration retains coins/RNG")
	check(Book.chef(migrated.save_data().state,id).cooking_speed==speed,"migration retains current speed")
	var corrupt:Dictionary=maximum.duplicate(true);corrupt.state.inventory.filter(func(c):return c.id==id)[0].growth_rate=9
	var guard:Dictionary=migrated.save_data();check(not migrated.restore(corrupt) and migrated.save_data()==guard,"inconsistent development rejected atomically")
	var poor=Session.new_session(9,{"starting_coins":0});var before:Dictionary=poor.save_data()
	check(poor.command({"type":"level_up_chef","chef_id":id,"expected_level":1}).reason=="not_enough_coins" and poor.save_data()==before,"unaffordable purchase atomic")
	print("Chef development: %s checks, %s failures"%[count,failures.size()]);quit(0 if failures.is_empty() else 1)
