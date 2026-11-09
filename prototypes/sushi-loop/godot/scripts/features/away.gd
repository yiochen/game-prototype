extends RefCounted
## Time away from the restaurant (#29). Owns the `away` slice. The restaurant
## does not simulate during an expedition or while the app is closed; all of
## that wall-clock time is one interval whose income is estimated from the
## committed restaurant and credited once when the restaurant resumes.
##
## Slice fields:
##   started          wall-clock start of the open interval, or null
##   credited_through end of the last credited interval; intervals never
##                    start before it, so nothing is credited twice
##   sequence         credited intervals so far
##   last             the latest credit {sequence, amount, seconds}, or null
## Balance: content/away.json. The estimate is a pure function of a service
## model the session builds from its layout (see GameSession._away_model).
const PATH := "res://content/away.json"
const MAX_INTEGER := 9007199254740991
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func initial() -> Dictionary:
	return {"started": null, "credited_through": null, "sequence": 0, "last": null}

static func is_open(state: Dictionary) -> bool:
	return state.get("away") is Dictionary and state.away.started != null

## Opens the interval at `now` unless one is already open.
static func begin(state: Dictionary, now: float) -> bool:
	var data: Dictionary = state.away
	if data.started != null: return false
	data.started = maxf(now, _floor(data))
	return true

## Seconds the open interval covers at `now`.
static func pending_seconds(state: Dictionary, now: float) -> float:
	var data: Dictionary = state.away
	if data.started == null: return 0.0
	return maxf(0.0, now - maxf(float(data.started), _floor(data)))

## Closes the interval at `now` and records `amount` as its one credit. A
## zero credit records nothing: the slice is as it was before the interval.
static func close(state: Dictionary, now: float, amount: int) -> Dictionary:
	var data: Dictionary = state.away
	var seconds := pending_seconds(state, now)
	data.started = null
	if amount <= 0: return {"sequence": int(data.sequence), "amount": 0, "seconds": seconds}
	data.credited_through = maxf(now, _floor(data))
	data.sequence = int(data.sequence) + 1
	data.last = {"sequence": int(data.sequence), "amount": amount, "seconds": seconds}
	return data.last.duplicate()

static func _floor(data: Dictionary) -> float:
	return -INF if data.credited_through == null else float(data.credited_through)

# ------------------------------------------------------------ estimate

## Coins earned over `seconds` by the restaurant `model` describes.
## model: {open, mode, belt_seconds, arrival_seconds, arrival_multiplier,
##   walk_speed, eating_seconds, sit_seconds, stand_seconds, preference_seconds,
##   dishes_per_visit, groups: [{chefs: [{rate, price}], seats: [{path, recipes}]}]}
## Each group is a set of chefs and the seats their belts reach. Supply is the
## chefs' loading rates, capped by the belt's one-dish-per-tile flow; demand
## is the seats' turnover, scaled down when arrivals cannot fill them. The
## estimate is aggregate: no individual guest or dish is simulated.
static func estimate(model: Dictionary, seconds: float) -> int:
	if seconds <= 0.0 or not model.get("open", false) or model.get("mode") == "edit": return 0
	var balance := definition()
	var dishes := float(model.dishes_per_visit)
	var seat_rates: Array = []
	var total_seat := 0.0
	for group in model.groups:
		var rates: Array = []
		for seat in group.seats:
			# A preference holds out for one dish of k on the menu for part of its countdown.
			var choices := maxf(1.0, float(seat.recipes))
			var waiting := (1.0 - 1.0 / choices) * float(model.preference_seconds) * float(balance.preference_delay_share)
			var walking := 2.0 * float(seat.path) / maxf(0.001, float(model.walk_speed))
			var visit := walking + float(model.sit_seconds) + float(model.stand_seconds) + dishes * float(model.eating_seconds) + waiting + float(balance.seat_turnover_seconds)
			rates.append(dishes / maxf(0.001, visit))
			total_seat += rates[-1]
		seat_rates.append(rates)
	if total_seat <= 0.0: return 0
	var arrivals := float(model.arrival_multiplier) / maxf(0.001, float(model.arrival_seconds)) * dishes
	var fill := minf(1.0, arrivals / total_seat)
	var income := 0.0
	for index in model.groups.size():
		var group: Dictionary = model.groups[index]
		var supply := 0.0
		var value := 0.0
		for chef in group.chefs:
			supply += float(chef.rate)
			value += float(chef.rate) * float(chef.price)
		if supply <= 0.0: continue
		var demand := 0.0
		for rate in seat_rates[index]: demand += float(rate) * fill
		var served := minf(minf(supply, 1.0 / maxf(0.001, float(model.belt_seconds))), demand)
		income += served * value / supply
	return mini(MAX_INTEGER, int(floor(income * float(balance.efficiency) * seconds)))

# ------------------------------------------------------------ save

static func valid(state: Dictionary) -> bool:
	var data: Variant = state.get("away")
	if not data is Dictionary: return false
	for field in ["started", "credited_through"]:
		if data.get(field) != null and not _finite(data[field]): return false
	if not _integer(data.get("sequence")): return false
	if data.credited_through != null and data.started != null and float(data.started) < float(data.credited_through): return false
	var last: Variant = data.get("last")
	if last == null: return int(data.sequence) == 0
	return last is Dictionary and _integer(last.get("sequence")) and int(last.sequence) == int(data.sequence) and _integer(last.get("amount")) and _finite(last.get("seconds")) and float(last.seconds) >= 0.0

static func normalize(state: Dictionary) -> void:
	state.away.sequence = int(state.away.sequence)
	if state.away.last is Dictionary:
		state.away.last.sequence = int(state.away.last.sequence)
		state.away.last.amount = int(state.away.last.amount)

static func _finite(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _integer(value: Variant) -> bool:
	return _finite(value) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER
