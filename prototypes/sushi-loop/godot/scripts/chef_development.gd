extends RefCounted
## Purchased development only. Tuning lives in content; no clock or RNG access.
const Book = preload("res://scripts/recipe_book.gd")
static var _balance: Dictionary = {}
static func balance() -> Dictionary:
	if _balance.is_empty(): _balance = JSON.parse_string(FileAccess.get_file_as_string("res://content/chef_development.json"))
	return _balance
static func cost(actor: Dictionary) -> int:
	return int(actor.get("level",1))*int(balance().upgrade_cost_per_level)
static func next_speed(actor: Dictionary) -> float:
	return float(actor.get("cooking_speed",1.0))+float(actor.get("growth_rate",balance().default_growth_rate))
static func tier(level: int) -> String:
	var result := "White"
	for i in range(Book.catalog().tiers.size()):
		if level>=int(Book.catalog().required_levels[i]): result=Book.catalog().tiers[i]
	return result
static func initialize(state: Dictionary) -> void:
	if not state.get("staff") is Dictionary or not state.get("inventory") is Array:return
	if not state.staff.has("dismissed"): state.staff.dismissed={}
	for stock in state.inventory:
		if not stock is Dictionary:return
		if stock.get("kind")!="chef":continue
		var actor:=Book.chef(state,str(stock.id))
		if actor.is_empty():continue
		if not actor.has("growth_rate"):actor.growth_rate=float(balance().growth_by_art.get(actor.get("art_id"),balance().default_growth_rate))
		if not actor.has("base_cooking_speed"):actor.base_cooking_speed=float(actor.cooking_speed)-(int(actor.level)-1)*float(actor.growth_rate)
		sync(state,actor)
static func sync(state: Dictionary, actor: Dictionary) -> void:
	for stock in state.inventory:
		if stock.get("id")==actor.id:
			for field in ["level","level_cap","cooking_speed","growth_rate","base_cooking_speed"]:stock[field]=actor[field]
static func valid(state: Dictionary) -> bool:
	if not state.get("staff") is Dictionary or not state.get("inventory") is Array:return false
	if not state.staff.get("dismissed") is Dictionary:return false
	for stock in state.inventory:
		if not stock is Dictionary or not stock.get("id") is String:return false
		if stock.get("kind")!="chef":continue
		var actor:=Book.chef(state,str(stock.id))
		if actor.is_empty():return false
		for field in ["growth_rate","base_cooking_speed"]:
			if not actor.get(field) is float and not actor.get(field) is int:return false
			if not is_finite(float(actor[field])) or stock.get(field)!=actor[field]:return false
		if float(actor.growth_rate)<=0 or absf(float(actor.cooking_speed)-(float(actor.base_cooking_speed)+(int(actor.level)-1)*float(actor.growth_rate)))>.000001:return false
	return true
static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	var actor:=Book.chef(state,str(request.get("chef_id","")))
	if actor.is_empty():return {"ok":false,"reason":"unknown_chef"}
	if request.type=="level_up_chef":
		var expected:Variant=request.get("expected_level")
		if not (expected is int or expected is float) or not is_finite(float(expected)) or float(expected)!=int(actor.level):return {"ok":false,"reason":"stale_level"}
		if int(actor.level)>=int(actor.level_cap):return {"ok":false,"reason":"chef_max"}
		var price:=cost(actor)
		if int(state.coins)<price:return {"ok":false,"reason":"not_enough_coins"}
		var recipe:Dictionary=config.recipes.get(actor.recipe_id,{})
		var old_duration:=Book.seconds(recipe,actor)
		var fraction:=clampf(float(actor.get("preparation_elapsed",0))/old_duration,0,1) if old_duration>0 else 0.0
		state.coins=int(state.coins)-price
		actor.level=int(actor.level)+1
		actor.cooking_speed=float(actor.base_cooking_speed)+(int(actor.level)-1)*float(actor.growth_rate)
		actor.preparation_elapsed=Book.seconds(recipe,actor)*(1.0 if actor.get("held_dish") is Dictionary else fraction)
		sync(state,actor)
		return {"ok":true,"level":actor.level,"cost":price,"chef_id":actor.id}
	if request.type=="fire_chef":
		var id:String=actor.id
		state.staff.dismissed[id]=str(actor.art_id)
		state.staff.hired.erase(id)
		if actor.get("held_dish") is Dictionary:state.discarded_dishes=int(state.discarded_dishes)+1
		state.objects=state.objects.filter(func(item):return item.id!=id)
		state.inventory=state.inventory.filter(func(item):return item.id!=id)
		if state.editor.selected_id==id:state.editor.selected_id=""
		return {"ok":true,"chef_id":id}
	return {"ok":false,"reason":"unknown_command"}
