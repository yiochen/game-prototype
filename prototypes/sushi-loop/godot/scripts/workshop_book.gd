extends RefCounted
## Workshop (#28): salvage buys independent equipment and power-up levels.
## Owns the `workshop` slice {levels, spent, seen}; the salvage balance stays in
## the expedition slice. Equipment: Hull (maximum hull), Harpoon (reeling
## strength: resistance drains faster), Collector (attraction range, capped,
## never a pickup-value multiplier). Power-ups: Shield (pickup duration),
## Passage (portal ride length), Shield at start (launch shield).
## Each Upgrade pays exactly one level; a replay token makes repeated taps and
## replayed commands pay once. A run copies `gear()` at Start, so upgrades never
## change an expedition already under way. Looks change at `looks` levels:
## equipment swaps a whole part sprite, power-ups change colour.
## Balance lives in res://content/workshop.json; the approved composition is
## design/workshop-preview/.
const PATH := "res://content/workshop.json"
const MAX_INTEGER := 9007199254740991
const TOKENS_KEPT := 40
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func tracks() -> Array:
	return definition().tracks

static func track(id: String) -> Dictionary:
	for entry in tracks():
		if entry.id == id: return entry
	return {}

static func initial() -> Dictionary:
	var levels := {}
	for entry in tracks(): levels[entry.id] = 1
	return {"levels": levels, "spent": [], "seen": {}}

static func max_level(id: String) -> int:
	return track(id).levels.size()

static func level(state: Dictionary, id: String) -> int:
	return int(state.workshop.levels.get(id, 1))

static func value(id: String, at: int) -> float:
	var values: Array = track(id).levels
	return float(values[clampi(at, 1, values.size()) - 1])

## Salvage for the next level, or -1 at the cap.
static func next_cost(state: Dictionary, id: String) -> int:
	var at := level(state, id)
	var costs: Array = track(id).costs
	return int(costs[at - 1]) if at - 1 < costs.size() else -1

## Look tier 1–3: base, first milestone, maximum.
static func tier(id: String, at: int) -> int:
	var result := 1
	for look in track(id).looks:
		if at >= int(look): result += 1
	return result

static func tier_color(t: int) -> Color:
	return Color(str(definition().tier_colors[clampi(t, 1, 3) - 1]))

## Values an expedition reads, copied into the run at Start.
static func gear(state: Dictionary) -> Dictionary:
	var result := {"tiers": {}}
	for entry in tracks():
		var at := level(state, entry.id)
		result[entry.id] = value(entry.id, at)
		result.tiers[entry.id] = tier(entry.id, at)
	return result

## The gear of a player who never bought anything.
static func base_gear() -> Dictionary:
	return gear({"workshop": initial()})

static func snapshot(state: Dictionary) -> Dictionary:
	var rows := []
	for entry in tracks():
		var at := level(state, entry.id)
		var cost := next_cost(state, entry.id)
		rows.append({"id": entry.id, "group": entry.group, "level": at, "max_level": entry.levels.size(), "max": cost < 0,
			"value": value(entry.id, at), "next_value": value(entry.id, at + 1) if cost >= 0 else value(entry.id, at),
			"cost": cost, "affordable": cost >= 0 and int(state.expedition.salvage) >= cost,
			"tier": tier(entry.id, at), "looks": entry.looks.duplicate(), "new": state.workshop.seen.get(entry.id) == false})
	return {"salvage": int(state.expedition.salvage), "tracks": rows, "gear": gear(state)}

static func command(state: Dictionary, request: Dictionary) -> Dictionary:
	var data: Dictionary = state.workshop
	match request.get("type"):
		"workshop_upgrade":
			var id := str(request.get("id", ""))
			if track(id).is_empty(): return {"ok": false, "reason": "unknown_track"}
			var token := str(request.get("token", ""))
			if token.is_empty(): return {"ok": false, "reason": "missing_token"}
			# A replayed or repeated request is accepted without paying again.
			if token in data.spent: return {"ok": true, "changed": false, "replayed": true}
			var cost := next_cost(state, id)
			if cost < 0: return {"ok": false, "reason": "max_level"}
			if int(state.expedition.salvage) < cost: return {"ok": false, "reason": "insufficient_salvage"}
			state.expedition.salvage = int(state.expedition.salvage) - cost
			var at := level(state, id) + 1
			data.levels[id] = at
			data.spent.append(token)
			if data.spent.size() > TOKENS_KEPT: data.spent = data.spent.slice(data.spent.size() - TOKENS_KEPT)
			var crossed: bool = at in track(id).looks.map(func(l): return int(l))
			if crossed: data.seen[id] = false
			return {"ok": true, "changed": true, "id": id, "level": at, "cost": cost, "new_look": crossed, "tier": tier(id, at)}
		"workshop_seen":
			# Leaving the Workshop acknowledges its NEW tags.
			if data.seen.is_empty(): return {"ok": true, "changed": false}
			data.seen = {}
			return {"ok": true, "changed": true}
	return {"ok": false, "reason": "unknown_command"}

static func valid(state: Dictionary) -> bool:
	var data = state.get("workshop")
	if not data is Dictionary or not data.get("levels") is Dictionary or not data.get("spent") is Array or not data.get("seen") is Dictionary: return false
	for entry in tracks():
		var at = data.levels.get(entry.id)
		if not (at is int or at is float) or float(at) != floorf(float(at)) or int(at) < 1 or int(at) > entry.levels.size(): return false
	for id in data.levels:
		if track(str(id)).is_empty(): return false
	for token in data.spent:
		if not token is String or token.is_empty(): return false
	for id in data.seen:
		if track(str(id)).is_empty() or data.seen[id] != false: return false
	return data.spent.size() <= TOKENS_KEPT

static func normalize(state: Dictionary) -> void:
	for id in state.workshop.levels: state.workshop.levels[id] = int(state.workshop.levels[id])
