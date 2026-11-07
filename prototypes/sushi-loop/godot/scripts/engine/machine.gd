extends RefCounted
## Small xstate-style lifecycle machines stored as plain JSON in a row:
## {"machine": state, "elapsed": seconds in state, "progress": 0..1}.
##
## A definition is data:
##   {"initial": "idle", "states": {
##     "idle":    {"on": {"assign": "working"}},
##     "working": {"progress": "duration", "done": "holding", "emit": "prepared"},
##     "holding": {"on": {"belt_free": "loading"}},
##     "loading": {"after": "loading_seconds", "to": "idle", "emit": "loaded"}}}
## "on" maps events to targets, or to {"to": target, "guard": name}.
## "after" counts seconds; "progress" advances a 0..1 fraction by
## dt / duration, so a speed change needs no rescaling. Durations and guards
## are resolved by name through the caller's `resolve(name, row)` callable.

static func start(definition: Dictionary, row: Dictionary, state := "") -> void:
	row.machine = definition.initial if state.is_empty() else state
	row.elapsed = 0.0
	row.progress = 0.0

static func is_in(row: Dictionary, state: String) -> bool:
	return str(row.get("machine", "")) == state

## Moves to the event's target when the current state accepts it.
static func send(definition: Dictionary, row: Dictionary, event: String, resolve := Callable()) -> bool:
	var transitions: Dictionary = definition.states.get(str(row.get("machine", "")), {}).get("on", {})
	if not transitions.has(event): return false
	var target = transitions[event]
	if target is Dictionary:
		if target.has("guard") and not (resolve.is_valid() and bool(resolve.call(str(target.guard), row))): return false
		target = target.to
	_enter(row, str(target))
	return true

## Advances timers by dt and follows completed transitions. Returns the names
## emitted on the way, in order. Leftover time carries into the next state.
static func step(definition: Dictionary, row: Dictionary, dt: float, resolve: Callable) -> Array:
	var emitted: Array = []
	var remaining := dt
	for guard in range(8):
		var state: Dictionary = definition.states.get(str(row.machine), {})
		row.elapsed = float(row.elapsed) + remaining
		if state.has("progress"):
			var duration := float(resolve.call(str(state.progress), row))
			var before := float(row.progress)
			row.progress = 1.0 if duration <= 0.0 else minf(1.0, before + remaining / duration)
			if float(row.progress) < 1.0: return emitted
			remaining = 0.0 if duration <= 0.0 else maxf(0.0, remaining - (1.0 - before) * duration)
			if not state.has("done"): return emitted
			if state.has("emit"): emitted.append(state.emit)
			_enter(row, str(state.done))
		elif state.has("after"):
			var seconds := float(resolve.call(str(state.after), row))
			if float(row.elapsed) + 0.000000001 < seconds: return emitted
			remaining = float(row.elapsed) - seconds
			if state.has("emit"): emitted.append(state.emit)
			_enter(row, str(state.to))
		else:
			return emitted
		if remaining <= 0.0: return emitted
	return emitted

static func valid(definition: Dictionary, row: Dictionary) -> bool:
	if not definition.states.has(row.get("machine")): return false
	for field in ["elapsed", "progress"]:
		var value = row.get(field)
		if not (value is float or value is int) or not is_finite(float(value)) or float(value) < 0.0: return false
	return float(row.progress) <= 1.0

static func _enter(row: Dictionary, state: String) -> void:
	row.machine = state
	row.elapsed = 0.0
	row.progress = 0.0
