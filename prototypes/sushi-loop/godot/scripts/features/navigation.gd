extends RefCounted
## Path search: breadth-first search on the restaurant grid, with no knowledge
## of guests, seats or any other feature. Callers choose destinations (a
## customer's stool, the exit, a wander target; later a waiter's guest) and
## pass cell sets; movement along a path stays with the walker's feature.
## See docs/state-architecture.md#navigation.

## Neighbour order decides which of several equal paths is found. It matches
## GameSession.DIRECTIONS (north, east, south, west) so routes never change.
const STEPS: Array[Vector2i] = [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

## Cells after `start`, up to and including the first goal reached, or [] if
## none is reachable (or `start` is itself the goal). A cell is enterable when
## it is in `open` and either not in `blocked` or one of the goals.
static func find_path(start: Vector2i, goals: Dictionary, open: Dictionary, blocked: Dictionary) -> Array:
	var frontier: Array[Vector2i] = [start]
	var previous: Dictionary = {start: start}
	var cursor := 0
	while cursor < frontier.size():
		var position := frontier[cursor]
		cursor += 1
		if goals.has(position):
			var result: Array = []
			var cell := position
			while cell != start:
				result.push_front({"x": cell.x, "y": cell.y})
				cell = previous[cell]
			return result
		for offset in STEPS:
			var neighbor: Vector2i = position + offset
			if previous.has(neighbor) or not open.has(neighbor) or (blocked.has(neighbor) and not goals.has(neighbor)):
				continue
			previous[neighbor] = position
			frontier.append(neighbor)
	return []

## Every cell reachable from each anchor, with its walking distance (the
## anchor's offset plus one per step) and the predecessor map to rebuild a
## route. Shorter distances win; ties keep the earlier anchor.
static func flood(anchors: Array, origin: Vector2, open: Dictionary, blocked: Dictionary) -> Dictionary:
	var reachable := {}
	for anchor in anchors:
		var frontier: Array[Vector2i] = [anchor]
		var previous := {anchor: anchor}
		var lengths := {anchor: origin.distance_to(Vector2(anchor))}
		var cursor := 0
		while cursor < frontier.size():
			var cell := frontier[cursor]
			cursor += 1
			var length := float(lengths[cell])
			if not reachable.has(cell) or length + 0.000001 < float(reachable[cell].length):
				reachable[cell] = {"length": length, "anchor": anchor, "previous": previous}
			for offset in STEPS:
				var neighbor: Vector2i = cell + offset
				if previous.has(neighbor) or not open.has(neighbor) or blocked.has(neighbor):
					continue
				previous[neighbor] = cell
				lengths[neighbor] = length + 1.0
				frontier.append(neighbor)
	return reachable

## The route from a flood's anchor to `target`, as path points.
static func route_to(reachable: Dictionary, target: Vector2i) -> Array:
	var record: Dictionary = reachable[target]
	var route: Array = []
	var cell := target
	while cell != record.anchor:
		route.push_front({"x": cell.x, "y": cell.y})
		cell = record.previous[cell]
	return route
