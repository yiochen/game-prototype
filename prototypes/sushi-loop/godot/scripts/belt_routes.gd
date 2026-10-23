extends RefCounted
## One explicit successor per tile. Incoming edges are derived, never inferred
## from mere proximity: adjacent independent routes remain independent.
const DIRECTIONS := {"north": Vector2i.UP, "east": Vector2i.RIGHT, "south": Vector2i.DOWN, "west": Vector2i.LEFT}

static func point(tile: Dictionary) -> Vector2i:
	return Vector2i(int(tile.x), int(tile.y))

static func by_id(objects: Array, identity: String) -> Dictionary:
	for tile in objects:
		if tile.kind == "belt" and tile.id == identity: return tile
	return {}

static func incoming(objects: Array, identity: String) -> Dictionary:
	for tile in objects:
		if tile.kind == "belt" and tile.get("next_id", "") == identity: return tile
	return {}

static func direction(delta: Vector2i) -> String:
	for key in DIRECTIONS:
		if DIRECTIONS[key] == delta: return key
	return ""

static func initialize(objects: Array) -> void:
	# Shipped pre-route saves used facing + adjacency. Preserve those links;
	# a legacy junction keeps the first input in saved object order. No tile,
	# dish, stock, coin or service clock is removed by this upgrade.
	for tile in objects:
		if tile.get("kind") == "belt":
			tile.next_id = ""
			tile.input_facing = tile.facing
	for tile in objects:
		if tile.get("kind") != "belt": continue
		for target in objects:
			if target.get("kind") != "belt" or point(target) != point(tile) + DIRECTIONS[tile.facing]: continue
			if not incoming(objects, target.id).is_empty() or DIRECTIONS[target.facing] == -DIRECTIONS[tile.facing]: continue
			tile.next_id = target.id
			target.input_facing = tile.facing
			break

static func valid(objects: Array) -> bool:
	var occupied := {}
	for tile in objects:
		if tile.kind != "belt": continue
		if not tile.get("next_id") is String or not DIRECTIONS.has(tile.get("input_facing")): return false
		if tile.next_id.is_empty(): continue
		var target := by_id(objects, tile.next_id)
		if target.is_empty() or target.id == tile.id or occupied.has(target.id): return false
		if point(target) != point(tile) + DIRECTIONS[tile.facing] or target.input_facing != tile.facing: return false
		occupied[target.id] = true
	for tile in objects:
		if tile.kind == "belt" and occupied.has(tile.id) and not tile.next_id.is_empty() and DIRECTIONS[tile.facing] == -DIRECTIONS[tile.input_facing]: return false
	return true

static func disconnect_output(tile: Dictionary) -> void:
	tile.next_id = ""
	tile.travel_elapsed = 0.0

static func detach(objects: Array, tile: Dictionary) -> void:
	var previous := incoming(objects, tile.id)
	if not previous.is_empty(): disconnect_output(previous)
	disconnect_output(tile)
	tile.input_facing = tile.facing

static func connect_tiles(objects: Array, source: Dictionary, target: Dictionary) -> void:
	var flow := direction(point(target) - point(source))
	# Reshaping replaces edges, never their old tiles or their contents.
	disconnect_output(source)
	var previous := incoming(objects, target.id)
	if not previous.is_empty(): disconnect_output(previous)
	if DIRECTIONS[source.input_facing] == -DIRECTIONS[flow]:
		previous = incoming(objects, source.id)
		if not previous.is_empty(): disconnect_output(previous)
		source.input_facing = flow
	source.facing = flow
	source.next_id = target.id
	target.input_facing = flow
	target.travel_elapsed = 0.0
	if DIRECTIONS[target.facing] == -DIRECTIONS[flow]:
		disconnect_output(target)
		target.facing = flow

static func vacating_tiles(objects: Array, eligible: Dictionary) -> Dictionary:
	# Resolve each chain/cycle once. A completely full long loop must not turn
	# the fixed-step simulation into a separate recursive traversal per plate.
	var tiles := {}
	for tile in objects:
		if tile.kind == "belt": tiles[tile.id] = tile
	var result := {}
	for identity in eligible:
		if result.has(identity): continue
		var chain: Array = []
		var seen := {}
		var cursor: String = identity
		var available := false
		while tiles.has(cursor):
			if result.has(cursor):
				available = result[cursor]
				break
			if tiles[cursor].dish == null or seen.has(cursor):
				available = true
				break
			if not eligible.has(cursor): break
			seen[cursor] = true
			chain.append(cursor)
			cursor = tiles[cursor].next_id
		for member in chain: result[member] = available
	return result
