extends RefCounted
## Tea pouring (#62): cup geometry -> volume, tilt -> flow, drips, the one-pour
## ending and grading. Pure and deterministic; the pour sheet (tea_pour.gd)
## steps it every frame and the session only records the finished grade.
## Each cup is an interior profile: half width r(y) and centre shift dx(y), y up
## from the interior floor in design px. A height slice holds pi * r^2, so the
## same flow rises quickly through narrow sections and slowly through wide ones.
## The shift only shears the silhouette; handles and feet hold nothing.
## Balance: content/tea.json. Approved composition: design/tea-pour-preview/.
const PATH := "res://content/tea.json"
const STEP := 0.5
const GRADES := ["ideal", "good", "under", "full", "overflow"]
static var _definition: Dictionary = {}
static var _cups: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func cup_ids() -> Array:
	return definition().cups.map(func(entry): return str(entry.id))

## Height tables for one cup, built once.
static func cup(id: String) -> Dictionary:
	if _cups.has(id): return _cups[id]
	var entry: Dictionary = {}
	for candidate in definition().cups:
		if candidate.id == id: entry = candidate
	if entry.is_empty(): return {}
	var height := float(entry.height)
	var radius: Array = entry.radius if entry.has("radius") else _chambers(entry.chambers)
	var shift: Array = entry.get("shift", [])
	var count := roundi(height / STEP)
	var radii := PackedFloat64Array(); radii.resize(count + 1)
	var shifts := PackedFloat64Array(); shifts.resize(count + 1)
	var volumes := PackedFloat64Array(); volumes.resize(count + 1)
	for index in range(count + 1):
		var y := index * STEP
		radii[index] = _smooth(radius, y)
		shifts[index] = _smooth(shift, y) if not shift.is_empty() else 0.0
		if index > 0: volumes[index] = volumes[index - 1] + PI * pow((radii[index - 1] + radii[index]) * 0.5, 2.0) * STEP
	var result := entry.duplicate(true)
	result.merge({"radii": radii, "shifts": shifts, "volumes": volumes, "capacity": volumes[count],
		"target_height": float(entry.target) * height}, true)
	result.target_volume = volume_at(result, result.target_height)
	_cups[id] = result
	return result

static func radius_at(c: Dictionary, y: float) -> float:
	return c.radii[clampi(roundi(y / STEP), 0, c.radii.size() - 1)]

static func shift_at(c: Dictionary, y: float) -> float:
	return c.shifts[clampi(roundi(y / STEP), 0, c.shifts.size() - 1)]

static func volume_at(c: Dictionary, y: float) -> float:
	var last: int = c.volumes.size() - 1
	var f := clampf(y / STEP, 0.0, float(last))
	var index := floori(f)
	if index >= last: return c.capacity
	return lerpf(c.volumes[index], c.volumes[index + 1], f - index)

## Liquid height for a volume.
static func level_for(c: Dictionary, volume: float) -> float:
	if volume <= 0.0: return 0.0
	if volume >= float(c.capacity): return float(c.height)
	var low := 0
	var high: int = c.volumes.size() - 1
	while high - low > 1:
		var middle := (low + high) >> 1
		if c.volumes[middle] < volume: low = middle
		else: high = middle
	return (low + (volume - c.volumes[low]) / (c.volumes[high] - c.volumes[low])) * STEP

## Height risen per unit of volume at y: 1 / area.
static func rise_rate(c: Dictionary, y: float) -> float:
	return 1.0 / (PI * pow(radius_at(c, y), 2.0))

static func flow_share(tilt: float) -> float:
	var pour: Dictionary = definition().pour
	var dead := float(pour.dead_zone)
	if tilt <= dead: return 0.0
	return pow((minf(1.0, tilt) - dead) / (1.0 - dead), float(pour.flow_curve))

# ---------------------------------------------------------------- one pour

static func new_pour(cup_id: String) -> Dictionary:
	return {"cup": cup_id, "volume": 0.0, "spilled": 0.0, "flow": 0.0, "drip": 0.0, "drip_left": 0.0, "was_flowing": false, "poured": false}

static func max_flow(c: Dictionary) -> float:
	return float(c.target_volume) / float(definition().pour.seconds_to_target_at_max)

## tilt: 0 upright .. 1 end of the arc. held: the player is still holding.
static func step(pour: Dictionary, delta: float, tilt: float, held: bool) -> void:
	var c := cup(str(pour.cup))
	var settings: Dictionary = definition().pour
	var share := flow_share(tilt) if held else 0.0
	# Stopping always leaves the same small trail of drops, whatever the flow was.
	if pour.was_flowing and share == 0.0: pour.drip_left = float(c.target_volume) * float(settings.drip_share)
	pour.was_flowing = share > 0.0
	var added := share * max_flow(c) * delta
	pour.drip = 0.0
	if share == 0.0 and float(pour.drip_left) > 0.0:
		var drop := minf(float(pour.drip_left), float(c.target_volume) * float(settings.drip_share) * delta / float(settings.drip_seconds))
		pour.drip_left = float(pour.drip_left) - drop
		pour.drip = drop / delta
		added += drop
	pour.flow = share
	if added > 0.0: pour.poured = true
	pour.volume = float(pour.volume) + added
	if float(pour.volume) > float(c.capacity):
		pour.spilled = float(pour.spilled) + float(pour.volume) - float(c.capacity)
		pour.volume = float(c.capacity)

static func level(pour: Dictionary) -> float:
	return level_for(cup(str(pour.cup)), float(pour.volume))

## One chance per request: tea has flowed, the flow is back to zero (released
## or eased back past the dead zone) and the trailing drops have landed.
static func done(pour: Dictionary) -> bool:
	return pour.poured and float(pour.flow) == 0.0 and float(pour.drip_left) <= 0.0

## Grade a finished pour. Bands are shares of the interior height around the line.
static func grade(pour: Dictionary) -> Dictionary:
	var c := cup(str(pour.cup))
	var bands: Dictionary = definition().grade
	var offset := (level(pour) - float(c.target_height)) / float(c.height)
	var fill := float(pour.volume) / float(c.target_volume)
	var id := "full"
	if float(pour.spilled) > 0.0: id = "overflow"
	elif absf(offset) <= float(bands.ideal_band): id = "ideal"
	elif absf(offset) <= float(bands.good_band): id = "good"
	elif offset < 0.0: id = "under"
	return {"id": id, "offset": offset, "fill": fill, "qualifies": qualifies(id, fill)}

## Whether a finished serving earns the tea tip bonus.
static func qualifies(grade_id: String, fill: float) -> bool:
	var bands: Dictionary = definition().grade
	if grade_id == "overflow": return bool(bands.overflow_qualifies)
	return fill >= float(bands.min_qualifying_fill)

# ---------------------------------------------------------------- profiles

static func _smooth(points: Array, y: float) -> float:
	if y <= float(points[0][0]): return float(points[0][1])
	for index in range(1, points.size()):
		var y1 := float(points[index][0])
		if y <= y1:
			var y0 := float(points[index - 1][0])
			var t := (y - y0) / (y1 - y0)
			var s := t * t * (3.0 - 2.0 * t)
			return lerpf(float(points[index - 1][1]), float(points[index][1]), s)
	return float(points[-1][1])

## Alternating round chambers joined by narrow throats.
static func _chambers(spec: Dictionary) -> Array:
	var result: Array = []
	var each := float(spec.height) / float(spec.count)
	for chamber in range(int(spec.count)):
		for index in range(9):
			if chamber > 0 and index == 0: continue
			var t := index / 8.0
			result.append([chamber * each + t * each, float(spec.narrow) + (float(spec.wide) - float(spec.narrow)) * pow(sin(PI * t), 0.8)])
	result.append([float(spec.height) + float(spec.neck), float(spec.narrow) + 2.0])
	return result
