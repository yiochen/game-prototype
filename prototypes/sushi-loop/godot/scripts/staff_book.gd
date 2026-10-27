extends RefCounted
## Pure applicant/roster rules. Caller supplies absolute time; offers never expire.
const PATH := "res://content/staff_catalog.json"
const Book = preload("res://scripts/recipe_book.gd")
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func initialize(config: Dictionary, state: Dictionary, seed_value := 1) -> void:
	if state.has("staff"): return
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value ^ 1649016
	state.staff = {"offers":[],"refresh_deadline":0.0,"generation":0,"next_offer_id":1,"next_hire_id":1,"hired":{},"random_state":str(rng.state)}
	for id in definition().initial_applicants: _offer(state.staff,str(id))
	for entry in state.inventory:
		if entry.kind == "chef": entry.staff_new = false

static func _offer(staff: Dictionary, identity: String) -> void:
	staff.offers.append({"id":"application-%s" % int(staff.next_offer_id),"applicant_id":identity})
	staff.next_offer_id = int(staff.next_offer_id)+1

static func snapshot(state: Dictionary) -> Dictionary:
	var result: Dictionary = state.staff.duplicate(true)
	result.capacity = int(definition().capacity)
	result.count = state.inventory.filter(func(entry): return entry.kind == "chef").size()
	for offer in result.offers:
		for field in definition().applicants[offer.applicant_id]: offer[field] = definition().applicants[offer.applicant_id][field]
	result.erase("random_state")
	return result

static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	var staff: Dictionary = state.staff
	match request.get("type"):
		"staff_seen":
			if not request.get("ids") is Array: return {"ok":false,"reason":"invalid_staff"}
			for id in request.ids:
				if not id is String or Book.chef(state,id).is_empty(): return {"ok":false,"reason":"unknown_chef"}
			for entry in state.inventory:
				if entry.kind == "chef" and entry.id in request.ids: entry.staff_new = false
			return {"ok":true}
		"refresh_applicants":
			var now: Variant = request.get("now")
			if not _number(now) or float(now)<0: return {"ok":false,"reason":"invalid_time"}
			if float(now)<float(staff.refresh_deadline): return {"ok":false,"reason":"refresh_cooldown"}
			var used: Array = staff.hired.values()
			var previous: Array = staff.offers.map(func(offer): return offer.applicant_id)
			var fresh: Array = definition().applicants.keys().filter(func(id): return not id in used)
			var rng := RandomNumberGenerator.new()
			rng.state = int(staff.random_state)
			for i in range(fresh.size()-1,0,-1):
				var j := rng.randi_range(0,i)
				var temp: Variant = fresh[i]; fresh[i] = fresh[j]; fresh[j] = temp
			# Prefer faces not in the remaining pool; fill to three without duplicates.
			var choices: Array = fresh.filter(func(id): return not id in previous)+fresh.filter(func(id): return id in previous)
			staff.offers = []
			for id in choices.slice(0,3): _offer(staff,str(id))
			staff.random_state = str(rng.state)
			staff.generation = int(staff.generation)+1
			staff.refresh_deadline = float(now)+float(definition().refresh_cooldown_seconds)
			return {"ok":true}
		"hire_applicant":
			var offer: Dictionary = {}
			for candidate in staff.offers:
				if candidate.id == request.get("offer_id"): offer = candidate
			if offer.is_empty(): return {"ok":false,"reason":"unknown_offer"}
			var data: Dictionary = definition().applicants[offer.applicant_id]
			if state.inventory.filter(func(entry): return entry.kind == "chef").size()>=int(definition().capacity): return {"ok":false,"reason":"staff_full"}
			if int(state.coins)<int(data.cost): return {"ok":false,"reason":"not_enough_coins"}
			var id := "hired-chef-%s" % int(staff.next_hire_id)
			var point:=Vector2i(-1,-1)
			for y in range(int(config.floor.get("backdrop_rows",0)),int(config.floor.rows)):
				for x in range(int(config.floor.columns)):
					if x!=int(config.floor.entrance.x) or y!=int(config.floor.entrance.y):point=Vector2i(x,y);break
				if point.x>=0:break
			if point.x<0:return {"ok":false,"reason":"invalid_floor"}
			var actor := {"id":id,"kind":"chef","name":str(data.name).get_slice(" ",0),"full_name":data.name,"art_id":data.art_id,"x":point.x,"y":point.y,"facing":"south","recipe_id":"","level":1,"level_cap":int(data.level_cap),"cooking_speed":float(data.cooking_speed),"growth_rate":float(data.growth_rate),"preparation_elapsed":0.0,"held_dish":null,"loading_elapsed":0.0,"visual_phase":"idle","visual_elapsed":0.0}
			state.inventory.append({"id":id,"kind":"chef","name":actor.name,"full_name":data.name,"art_id":data.art_id,"recipe_id":"","level":1,"level_cap":actor.level_cap,"cooking_speed":actor.cooking_speed,"growth_rate":actor.growth_rate,"count":1,"assigned":false,"facing":"south","stored_object":actor,"staff_new":true})
			state.coins = int(state.coins)-int(data.cost)
			staff.hired[id] = offer.applicant_id
			staff.next_hire_id = int(staff.next_hire_id)+1
			staff.offers.erase(offer)
			return {"ok":true,"chef_id":id,"offer_id":offer.id,"applicant_id":offer.applicant_id,"cost":int(data.cost)}
	return {"ok":false,"reason":"unknown_command"}

static func valid(config: Dictionary, state: Dictionary) -> bool:
	if not state.get("staff") is Dictionary: return false
	var staff: Dictionary = state.staff
	if not staff.get("offers") is Array or staff.offers.size()>3 or not staff.get("hired") is Dictionary: return false
	for key in ["generation","next_offer_id","next_hire_id"]:
		if not _integer(staff.get(key)) or int(staff[key])<(0 if key=="generation" else 1): return false
	if not _number(staff.get("refresh_deadline")) or float(staff.refresh_deadline)<0: return false
	if not staff.get("random_state") is String or not staff.random_state.is_valid_int() or str(int(staff.random_state))!=staff.random_state: return false
	var identities := {}; var offers := {}
	for offer in staff.offers:
		if not offer is Dictionary or not offer.get("id") is String or not offer.id.begins_with("application-") or not definition().applicants.has(offer.get("applicant_id")): return false
		var number := str(offer.id).trim_prefix("application-")
		if not number.is_valid_int() or int(number)<1 or int(number)>=int(staff.next_offer_id) or str(int(number))!=number or offers.has(offer.id) or identities.has(offer.applicant_id): return false
		offers[offer.id] = true; identities[offer.applicant_id] = true
	for id in staff.hired:
		if not id is String or not id.begins_with("hired-chef-") or not definition().applicants.has(staff.hired[id]) or identities.has(staff.hired[id]): return false
		var index := str(id).trim_prefix("hired-chef-")
		if not index.is_valid_int() or int(index)<1 or int(index)>=int(staff.next_hire_id) or str(int(index))!=index: return false
		identities[staff.hired[id]] = true
		var actor := Book.chef(state,id)
		var data: Dictionary = definition().applicants[staff.hired[id]]
		if actor.is_empty() or actor.get("art_id")!=data.art_id or actor.get("level_cap")!=data.level_cap or actor.get("growth_rate")!=data.growth_rate: return false
	for entry in state.get("inventory",[]):
		if entry.get("kind") == "chef" and not entry.get("staff_new") is bool: return false
	return true

static func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))
static func _integer(value: Variant) -> bool:
	return _number(value) and float(value)>=0 and float(value)==floor(float(value)) and float(value)<=9007199254740991.0
