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
