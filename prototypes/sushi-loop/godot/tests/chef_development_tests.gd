extends SceneTree
const Session=preload("res://scripts/session.gd")
const Book=preload("res://scripts/recipe_book.gd")
const Development=preload("res://scripts/chef_development.gd")
const Chefs=preload("res://scripts/features/chefs.gd")
const Store=preload("res://scripts/engine/store.gd")
var count:=0
var failures:Array[String]=[]
func check(value:bool,message:String)->void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func _initialize()->void:call_deferred("run")
## The chef as the rules see it: one record in the store, speed calculated.
func chef(session,id:String)->Dictionary:return Chefs.record(session._store,session._configuration,id)
func run()->void:
	var session=Session.new_session(81,{"starting_coins":10000})
	var initial:Dictionary=GameSession.flat_view(session.save_data())
	var id:String=session.snapshot().objects.filter(func(c):return c.kind=="chef")[0].id
	var actor:=chef(session,id)
	var start:int=actor.level
	var growth:float=actor.growth_rate
	var speed:float=actor.cooking_speed
	var price:=Development.cost(actor)
	check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":start}).ok,"one level purchase")
	actor=chef(session,id)
	check(actor.level==start+1 and absf(actor.cooking_speed-speed-growth)<.000001,"configured growth applies once")
	check(session.snapshot().coins==10000-price,"single debit")
	var bought:Dictionary=session.save_data()
	check(not session.command({"type":"level_up_chef","chef_id":id,"expected_level":start}).ok and session.save_data()==bought,"replayed input is atomic")
	check(not session.command({"type":"level_up_chef","chef_id":id}).ok and session.save_data()==bought,"preview level required")
	check(session.snapshot().recipes==initial.configuration.recipes,"chef development never changes fixed prices/recipes")
	check(session.save_data().random_state==initial.random_state and session.snapshot().elapsed==0,"purchase does not advance clock or RNG")
	while actor.level<3:
		check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"buy tier threshold")
		actor=chef(session,id)
	check(session.command({"type":"discover_recipe","recipe_id":"tamago_nigiri"}).ok and session.command({"type":"prepare_recipe","chef_id":id,"recipe_id":"tamago_nigiri"}).ok,"Yellow unlock grants actual preparation eligibility")
	var time_before:float=session.snapshot().objects.filter(func(c):return c.id==id)[0].preparation_seconds
	session.advance(.5)
	check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"upgrade while preparation underway")
	var active:Dictionary=session.snapshot().objects.filter(func(c):return c.id==id)[0]
	check(active.preparation_seconds<time_before and active.preparation>0,"actual preparation duration improves, fractional work preserved")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(session.save_data()))),"upgraded preparation restores")
	actor=chef(session,id)
	var upgraded:Dictionary=actor.duplicate(true)
	check(session.command({"type":"unassign_chef","chef_id":id}).ok,"unassign works from Live")
	actor=chef(session,id)
	for field in ["level","level_cap","growth_rate","base_cooking_speed","cooking_speed"]:check(actor[field]==upgraded[field],"unassign retains "+field)
	check(not session.command({"type":"prepare_recipe","chef_id":id,"recipe_id":"salmon_nigiri"}).ok,"stored chef cannot prepare")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(session.save_data()))),"stored upgraded chef restores")
	var stored:Dictionary=session.save_data()
	check(not session.command({"type":"staff_place","inventory_id":id,"x":0,"y":3}).ok and session.save_data()==stored,"invalid reassignment is atomic")
	check(session.command({"type":"staff_place","inventory_id":id,"x":1,"y":5}).ok,"valid reassignment uses existing placement")
	actor=chef(session,id)
	check(actor.level==upgraded.level and actor.cooking_speed==upgraded.cooking_speed,"reassignment retains development")
	check(actor.recipe_id=="" and actor.held_dish==null and actor.preparation_elapsed==0,"reassigned chef waits for explicit Prepare")
	while int(actor.level)<int(actor.level_cap):
		check(session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok,"development to cap")
		actor=chef(session,id)
	var maximum:Dictionary=GameSession.flat_view(session.save_data())
	check(not session.command({"type":"level_up_chef","chef_id":id,"expected_level":actor.level}).ok and GameSession.flat_view(session.save_data())==maximum,"MAX cannot exceed cap or debit")
	check(Development.tier(3)=="Yellow" and Development.tier(5)=="Red" and Development.tier(8)=="Blue" and Development.tier(12)=="Black","shared tier thresholds")
	for assigned in [true,false]:
		var firing=Session.new();check(firing.restore(maximum),"restore fire fixture")
		if not assigned:check(firing.command({"type":"unassign_chef","chef_id":id}).ok,"unassigned fire setup")
		var coins:int=firing.snapshot().coins
		check(firing.command({"type":"fire_chef","chef_id":id}).ok and not Chefs.exists(firing._store,id),"fire removes assigned/stored chef")
		check(firing.snapshot().coins==coins,"fire never refunds")
		var removed:Dictionary=firing.save_data()
		check(not firing.command({"type":"fire_chef","chef_id":id}).ok and firing.save_data()==removed,"repeated Fire cannot remove another chef")
		check(Session.new().restore(JSON.parse_string(JSON.stringify(removed))),"dismissal of starter survives reopening")
	var hire=Session.new_session(7,{"starting_coins":1000})
	var hire_result:Dictionary=hire.command({"type":"hire_applicant","offer_id":hire.snapshot().staff.offers[0].id})
	check(hire_result.ok and hire.command({"type":"fire_chef","chef_id":hire_result.chef_id}).ok,"hired chef can be permanently fired")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(hire.save_data()))),"fired hired mapping restores")
	var migrated=Session.new_session(1)
	var corrupt:Dictionary=maximum.duplicate(true);corrupt.engine.worlds.restaurant.tables.development.rows[id].level=0
	var guard:Dictionary=migrated.save_data();check(not migrated.restore(corrupt) and migrated.save_data()==guard,"inconsistent development rejected atomically")
	var derived:Dictionary=maximum.duplicate(true);derived.engine.worlds.restaurant.tables.development.rows[id].cooking_speed=9.0
	check(not migrated.restore(derived) and migrated.save_data()==guard,"a save storing a calculated speed is rejected")
	check(not maximum.engine.worlds.restaurant.tables.development.rows[id].has("cooking_speed") and not maximum.state.objects.any(func(o):return o.has("level")),"chef speed and records are saved once, in the store")
	var poor=Session.new_session(9,{"starting_coins":0});var before:Dictionary=poor.save_data()
	check(poor.command({"type":"level_up_chef","chef_id":id,"expected_level":1}).reason=="not_enough_coins" and poor.save_data()==before,"unaffordable purchase atomic")
	# A finished dish clamps elapsed to the in-memory duration; after JSON the
	# recomputed duration may be an ulp shorter. Saves must still reopen.
	var reopened:=true
	for trial in range(1,12):
		var cooking=Session.new_session(trial,{"starting_coins":100000});cooking.command({"type":"set_mode","mode":"live"})
		for step in range(11):
			cooking.advance(.37*trial)
			if not cooking.command({"type":"level_up_chef","chef_id":id,"expected_level":chef(cooking,id).level}).ok:break
			reopened=reopened and Session.new().restore(JSON.parse_string(JSON.stringify(cooking.save_data(),"",true,true)))
	check(reopened,"level-up beside a finished dish survives saving")
	print("Chef development: %s checks, %s failures"%[count,failures.size()]);quit(0 if failures.is_empty() else 1)
