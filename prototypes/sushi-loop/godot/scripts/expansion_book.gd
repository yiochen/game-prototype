extends RefCounted
## Approved #19 whole-object clearance. Content owns masks, prices and artwork.
const PATH := "res://content/expansion.json"
const VERSION := 2
static var _content: Dictionary = {}
static var _patches: Dictionary = {}
static var _cells: Dictionary = {}
static var _dock: Dictionary = {}
static var _dock_ids: Array = []
static var _area_geometry: Dictionary = {}
static var _area_mutex := Mutex.new()

static func definition() -> Dictionary:
	if _content.is_empty():
		_content = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		for c in _content.dock_cells: _dock[Vector2i(int(c[0]),int(c[1]))] = true
		for value in _content.patches:
			_patches[str(value.id)] = value
			for y in range(int(value.y),int(value.y)+int(value.h)):
				for x in range(int(value.x),int(value.x)+int(value.w)): _cells[Vector2i(x,y)] = value
		for c in _dock:
			for dy in range(-1,2):
				for dx in range(-1,2):
					var near: Vector2i = c+Vector2i(dx,dy)
					if not _dock.has(near) and _cells.has(near) and not _cells[near].id in _dock_ids: _dock_ids.append(_cells[near].id)
	return _content

static func enabled(floor_data: Dictionary) -> bool:
	return int(floor_data.get("backdrop_rows",0)) == 3 and int(floor_data.get("world_columns",0)) >= 21 and int(floor_data.get("columns",0)) >= 7

static func columns(floor_data: Dictionary) -> int:
	return maxi(int(floor_data.world_columns),int(floor_data.columns)+14) if enabled(floor_data) else int(floor_data.columns)

static func offset(floor_data: Dictionary) -> int:
	return maxi(0,int(floor_data.columns)-7) if enabled(floor_data) else 0

static func patch(identity: String, floor_data: Dictionary = {}) -> Dictionary:
	definition()
	var value: Dictionary = _patches.get(identity,{})
	if value.is_empty() or floor_data.is_empty() or offset(floor_data) == 0: return value
	var result: Dictionary = value.duplicate(true);result.x = int(result.x)+offset(floor_data)
	return result

static func contains(value: Dictionary, cell: Vector2i) -> bool:
	return cell.x >= int(value.x) and cell.x < int(value.x)+int(value.w) and cell.y >= int(value.y) and cell.y < int(value.y)+int(value.h)

static func dock_cell(cell: Vector2i) -> bool:
	definition()
	return _dock.has(cell)

static func dock_blockers(state: Dictionary) -> Array:
	definition()
	return _dock_ids.filter(func(id): return not id in state.get("expansion",{}).get("cleared",[]))

static func dock_ready(state: Dictionary) -> bool:
	return state.has("expansion") and dock_blockers(state).is_empty()

static func dock_open(state: Dictionary) -> bool:
	return dock_ready(state) and state.expansion.get("revealed",false) == true

static func usable(state: Dictionary, floor_data: Dictionary, cell: Vector2i, placement := false) -> bool:
	if cell.x < 0 or cell.x >= columns(floor_data) or cell.y < int(floor_data.get("backdrop_rows",0)) or cell.y >= int(floor_data.rows): return false
	if not enabled(floor_data): return true
	var local := Vector2i(cell.x-offset(floor_data),cell.y)
	if dock_cell(local): return not placement and dock_open(state)
	if cell.x < int(floor_data.columns): return true
	definition()
	if _cells.has(local): return str(_cells[local].id) in state.get("expansion",{}).get("cleared",[])
	# Legacy rooms with extra rows keep those rows; nothing is removed or moved.
	return true

static func neighboring(state: Dictionary, floor_data: Dictionary, value: Dictionary) -> bool:
	if value.is_empty() or str(value.id) in state.get("expansion",{}).get("cleared",[]): return false
	for y in range(int(value.y),int(value.y)+int(value.h)):
		if usable(state,floor_data,Vector2i(int(value.x)-1,y)) or usable(state,floor_data,Vector2i(int(value.x)+int(value.w),y)): return true
	for x in range(int(value.x),int(value.x)+int(value.w)):
		if usable(state,floor_data,Vector2i(x,int(value.y)-1)) or usable(state,floor_data,Vector2i(x,int(value.y)+int(value.h))): return true
	return false

static func _geometry(floor_data: Dictionary) -> Dictionary:
	# Only floor geometry is shared. Clearance belongs to each session and is
	# read below, so other restaurants, restores and legacy sizes stay independent.
	var key := Vector4i(int(floor_data.columns),columns(floor_data),int(floor_data.rows),int(floor_data.get("backdrop_rows",0)))
	_area_mutex.lock()
	if _area_geometry.has(key):
		var cached: Dictionary = _area_geometry[key]
		_area_mutex.unlock()
		return cached
	var initial := 0
	var counts := {}
	var empty := {"expansion":{"cleared":[]}}
	for y in range(key.w,key.z):
		for x in range(key.y):
			var cell := Vector2i(x,y)
			if usable(empty,floor_data,cell,true): initial += 1
			else:
				var local := Vector2i(x-offset(floor_data),y)
				if _cells.has(local) and not dock_cell(local):
					var id: String = str(_cells[local].id)
					counts[id] = int(counts.get(id,0))+1
	var result := {"base":initial,"patch_cells":counts}
	_area_geometry[key] = result
	_area_mutex.unlock()
	return result

static func area(state: Dictionary, floor_data: Dictionary) -> int:
	if not enabled(floor_data): return columns(floor_data)*maxi(0,int(floor_data.rows)-int(floor_data.get("backdrop_rows",0)))
	var geometry := _geometry(floor_data)
	var result: int = geometry.base
	var cleared: Array = state.get("expansion",{}).get("cleared",[])
	for id in geometry.patch_cells:
		if id in cleared: result += int(geometry.patch_cells[id])
	return result

static func base_area(floor_data: Dictionary) -> int:
	return int(_geometry(floor_data).base) if enabled(floor_data) else area({},floor_data)

static func staff_bonus(state: Dictionary, floor_data: Dictionary) -> int:
	return maxi(0,(area(state,floor_data)-base_area(floor_data))/int(definition().staff_cells_per_slot))

static func arrival_multiplier(state: Dictionary, floor_data: Dictionary) -> float:
	return float(area(state,floor_data))/maxi(1,base_area(floor_data))

static func initialize(config: Dictionary, state: Dictionary) -> void:
	if not enabled(config.floor) or state.has("expansion"): return
	config.floor.world_columns = columns(config.floor)
	state.expansion = {"version":VERSION,"cleared":[],"revealed":false}
	for value in definition().patches:
		var physical := patch(str(value.id),config.floor)
		var preserve: bool = int(physical.x) < int(config.floor.columns)
		for object in state.objects:
			if contains(physical,Vector2i(int(object.x),int(object.y))): preserve = true
		if preserve: state.expansion.cleared.append(value.id)

static func migrate_v1(state: Dictionary) -> bool:
	# Version 1 automatically revealed the dock. Preserve that already-visible
	# result without replaying it, while new clears now require confirmation.
	var previous: Variant = state.get("expansion")
	if not previous is Dictionary or previous.get("version") != 1 or not previous.get("cleared") is Array or previous.has("revealed"): return false
	previous.version = VERSION
	previous.revealed = dock_ready(state)
	return true

static func valid(config: Dictionary, state: Dictionary) -> bool:
	if not enabled(config.floor): return not state.has("expansion")
	if int(config.floor.world_columns) < columns(config.floor): return false
	var expansion: Variant = state.get("expansion")
	if not expansion is Dictionary or expansion.get("version") != VERSION or not expansion.get("cleared") is Array: return false
	if not expansion.get("revealed") is bool or (expansion.revealed and not dock_ready(state)): return false
	var seen := {}
	for id in expansion.cleared:
		if not id is String or patch(id).is_empty() or seen.has(id): return false
		seen[id] = true
	for object in state.objects:
		if not usable(state,config.floor,Vector2i(int(object.x),int(object.y)),true): return false
	return true

static func snapshot(config: Dictionary, state: Dictionary) -> Dictionary:
	if not enabled(config.floor): return {"enabled":false}
	var remaining: Array = []
	for value in definition().patches:
		if str(value.id) in state.expansion.cleared: continue
		var entry: Dictionary = patch(str(value.id),config.floor).duplicate(true)
		entry.available = neighboring(state,config.floor,entry)
		remaining.append(entry)
	var usable_area := area(state,config.floor)
	var initial := base_area(config.floor)
	return {"enabled":true,"offset_x":offset(config.floor),"cleared":state.expansion.cleared.duplicate(),"patches":remaining,"dock_ready":dock_ready(state),"dock_open":dock_open(state),"dock_blockers":dock_blockers(state),"usable_area":usable_area,"base_area":initial,"arrival_multiplier":float(usable_area)/maxi(1,initial),"staff_bonus":maxi(0,(usable_area-initial)/int(definition().staff_cells_per_slot))}

static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	if not enabled(config.floor): return {"ok":false,"reason":"clearance_unavailable"}
	if request.get("type") == "reveal_dock":
		if dock_open(state): return {"ok":true,"changed":false}
		if not dock_ready(state): return {"ok":false,"reason":"surrounding_trash"}
		state.expansion.revealed = true
		return {"ok":true,"changed":true}
	if request.get("type") == "dock_access":
		if not dock_ready(state): return {"ok":false,"reason":"surrounding_trash"}
		if not dock_open(state): return {"ok":false,"reason":"covered"}
		if not request.get("destination") in ["Submarine","Workshop"]: return {"ok":false,"reason":"unknown_destination"}
		return {"ok":true,"changed":false,"destination":request.destination}
	var value := patch(str(request.get("id","")),config.floor)
	if value.is_empty(): return {"ok":false,"reason":"unknown_trash"}
	if value.id in state.expansion.cleared: return {"ok":true,"changed":false}
	if not neighboring(state,config.floor,value): return {"ok":false,"reason":"not_neighboring"}
	if int(state.coins) < int(value.price): return {"ok":false,"reason":"not_enough_coins"}
	state.coins = int(state.coins)-int(value.price)
	state.expansion.cleared.append(value.id)
	return {"ok":true,"changed":true,"id":value.id}
