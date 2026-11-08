extends RefCounted
## Tips (#61): optional bonus income from attentive service. Owns the `tips`
## slice: cash piles on the floor and the tip jar's level and balance. A tip is
## decided once per visit, when a guest who bought food gets up to leave. Visit
## facts it needs (bill, tea, the requested dish) are fields of the guest's
## transient `customer` row. Balance lives in content/tips.json.
## Randomness is derived from the slice's salt and the guest id, so tips never
## draw from (or shift) the restaurant's shared generator.
const PATH := "res://content/tips.json"
const MAX_INTEGER := 9007199254740991
const TEA_PHASES := ["none", "requested", "served", "skipped", "missed"]
## Defaults for the visit fields, so rows saved before #61 load unchanged.
const VISIT_FIELDS := {"bill": 0, "tea_phase": "none", "tea_elapsed": 0.0, "requested_dish_id": "", "request_eaten": false, "tip_evaluated": false}
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func initial(salt: int) -> Dictionary:
	return {"salt": salt, "cash": [], "jar": {"level": 0, "balance": 0}}

# ---------------------------------------------------------------- balance

static func capacity(level: int) -> int:
	var values: Array = definition().jar.capacities
	return int(values[clampi(level, 0, values.size() - 1)])

static func max_level() -> int:
	return definition().jar.capacities.size() - 1

## Cost of the next upgrade from `level`, or -1 at the top level.
static func upgrade_cost(level: int) -> int:
	var costs: Array = definition().jar.upgrade_costs
	return int(costs[level]) if level < costs.size() else -1

static func chance(customer: Dictionary) -> float:
	var values: Dictionary = definition().chance
	if customer.get("request_eaten", false): return float(values.requested_dish)
	if customer.get("tea_phase") == "served": return minf(1.0, float(values.base) + float(values.tea_bonus))
	return float(values.base)

static func amount(bill: int) -> int:
	return maxi(1, roundi(float(bill) * float(definition().tip_share)))

## Pile art for an amount: 0 one note, 1 three notes, 2 a bundle.
static func tier(value: int) -> int:
	var piles: Dictionary = definition().piles
	return 2 if value > int(piles.bundle_above) else 1 if value > int(piles.three_notes_above) else 0

## A stable value in [0, 1) for one guest and purpose.
static func roll(state: Dictionary, customer_id: String, purpose: String) -> float:
	var generator := RandomNumberGenerator.new()
	generator.seed = hash([int(state.tips.salt), customer_id, purpose])
	return generator.randf()

# ---------------------------------------------------------------- jar

static func jar_owned(state: Dictionary) -> bool:
	return int(state.get("shop", {}).get("purchased", {}).get(definition().jar.inventory_id, 0)) > 0

static func jar_object(objects: Array) -> Dictionary:
	for object in objects:
		if object.get("kind") == "decor" and object.get("art_id") == definition().jar.art_id: return object
	return {}

static func jar_room(state: Dictionary) -> int:
	return maxi(0, capacity(int(state.tips.jar.level)) - int(state.tips.jar.balance))

## The Shop's next jar upgrade, once a jar is owned and not at its top level.
static func upgrade_offer(state: Dictionary) -> Dictionary:
	if not jar_owned(state): return {}
	var level := int(state.tips.jar.level)
	if upgrade_cost(level) < 0: return {}
	return {"id": "tip-jar-upgrade", "kind": "tip_upgrade", "name": "Bigger tip jar", "art_id": definition().jar.art_id,
		"description": "Holds $%d of tips instead of $%d." % [capacity(level + 1), capacity(level)],
		"cost": upgrade_cost(level), "remaining": null, "level": level}

# ---------------------------------------------------------------- floor cash

static func pile_at(state: Dictionary, cell: Vector2i) -> int:
	for index in range(state.tips.cash.size()):
		var pile: Dictionary = state.tips.cash[index]
		if int(pile.x) == cell.x and int(pile.y) == cell.y: return index
	return -1

## The eight tiles around `center`, in a fixed order.
static func around(center: Vector2i) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			if dx != 0 or dy != 0: result.append(center + Vector2i(dx, dy))
	return result

## Removes every pile within the collect radius of the tapped pile and returns
## them; the caller credits the total. Empty if no pile is at `cell`.
static func take_around(state: Dictionary, cell: Vector2i) -> Array:
	if pile_at(state, cell) < 0: return []
	var radius := int(definition().collect_radius_cells)
	var taken: Array = []
	var kept: Array = []
	for pile in state.tips.cash:
		if absi(int(pile.x) - cell.x) <= radius and absi(int(pile.y) - cell.y) <= radius: taken.append(pile)
		else: kept.append(pile)
	state.tips.cash = kept
	return taken

static func total(piles: Array) -> int:
	var sum := 0
	for pile in piles: sum += int(pile.amount)
	return sum

# ---------------------------------------------------------------- view and rules

static func snapshot(state: Dictionary, objects: Array) -> Dictionary:
	var jar := jar_object(objects)
	var level := int(state.tips.jar.level)
	var piles: Array = []
	for pile in state.tips.cash: piles.append({"x": int(pile.x), "y": int(pile.y), "amount": int(pile.amount), "tier": tier(int(pile.amount))})
	return {"cash": piles, "jar": {
		"owned": jar_owned(state), "placed": not jar.is_empty(), "id": str(jar.get("id", "")),
		"x": int(jar.get("x", 0)), "y": int(jar.get("y", 0)),
		"level": level, "max_level": max_level(), "balance": int(state.tips.jar.balance), "capacity": capacity(level),
		"upgrade_cost": upgrade_cost(level), "next_capacity": capacity(level + 1) if level < max_level() else 0,
	}}

static func valid(state: Dictionary) -> bool:
	var tips: Variant = state.get("tips")
	if not tips is Dictionary or not _integer(tips.get("salt")) or not tips.get("cash") is Array or not tips.get("jar") is Dictionary: return false
	var cells := {}
	for pile in tips.cash:
		if not pile is Dictionary or not _integer(pile.get("x")) or not _integer(pile.get("y")) or not _integer(pile.get("amount")) or int(pile.amount) < 1: return false
		var cell := Vector2i(int(pile.x), int(pile.y))
		if cells.has(cell): return false
		cells[cell] = true
	if not _integer(tips.jar.get("level")) or int(tips.jar.level) > max_level() or not _integer(tips.jar.get("balance")): return false
	if int(tips.jar.balance) > capacity(int(tips.jar.level)): return false
	# Upgrades and money need a jar that was bought.
	return jar_owned(state) or (int(tips.jar.level) == 0 and int(tips.jar.balance) == 0)

static func valid_visit(customer: Dictionary) -> bool:
	if not _integer(customer.get("bill")) or not customer.get("tea_phase") in TEA_PHASES or not customer.get("requested_dish_id") is String: return false
	if not customer.get("request_eaten") is bool or not customer.get("tip_evaluated") is bool: return false
	var clock: Variant = customer.get("tea_elapsed")
	if not (clock is float or clock is int) or not is_finite(float(clock)) or float(clock) < 0.0: return false
	# A tip is decided only on leaving, and only food that was paid for earns one.
	if customer.tip_evaluated and customer.get("phase") != "leaving": return false
	return not customer.request_eaten or int(customer.bill) > 0

static func normalize(state: Dictionary) -> void:
	state.tips.salt = int(state.tips.salt)
	state.tips.jar.level = int(state.tips.jar.level)
	state.tips.jar.balance = int(state.tips.jar.balance)
	for pile in state.tips.cash:
		for key in ["x", "y", "amount"]: pile[key] = int(pile[key])

static func _integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER
