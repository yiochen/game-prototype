extends RefCounted
## Cosmetics only. Isolated stock RNG never advances restaurant service RNG.
const VERSION := 1
const Expansion = preload("res://scripts/expansion_book.gd")
const MAX_INTEGER := 9007199254740991
static var _content: Dictionary = {}
static func definition() -> Dictionary:
	if _content.is_empty(): _content = JSON.parse_string(FileAccess.get_file_as_string("res://content/floor_styles.json"))
	return _content
static func style(id: String) -> Dictionary:
	for entry in definition().styles:
		if entry.id == id: return entry
	return {}
static func initialize(state: Dictionary, seed_value: int) -> void:
	state.floor_styles = {"owned":["cream"],"painted":{},"purchase_sequence":0,"seed":posmod(seed_value,2147483647),"rotation":0,"offer":""}
	_choose(state.floor_styles)
static func _choose(data: Dictionary) -> void:
	data.offer = ""
	var rng := RandomNumberGenerator.new()
	rng.seed = int(data.seed)+int(data.rotation)*104729
	if rng.randf() >= float(definition().offer_chance): return
	var eligible: Array = definition().styles.filter(func(s): return s.id not in data.owned)
	var total := 0.0
	for band in definition().bands:
		if eligible.any(func(s): return s.band == band.id): total += float(band.weight)
	if total <= 0: return
	var roll := rng.randf()*total
	for band in definition().bands:
		var candidates: Array = eligible.filter(func(s): return s.band == band.id)
		if candidates.is_empty(): continue
		roll -= float(band.weight)
		if roll <= 0:
			data.offer = candidates[rng.randi_range(0,candidates.size()-1)].id
			return
static func snapshot(state: Dictionary) -> Dictionary:
	var result: Dictionary = state.floor_styles.duplicate(true)
	result.entries = []
	for id in result.owned:
		var entry := style(id).duplicate(true)
		entry.kind = "floor";entry.count = 1;entry.available = true;entry.style_id = id;entry.art_id = "floor-"+id
		result.entries.append(entry)
	return result
static func offer(state: Dictionary) -> Dictionary:
	var id: String = state.floor_styles.offer
	if id.is_empty(): return {}
	var entry := style(id).duplicate(true)
	entry.id = "floor:"+id;entry.style_id = id;entry.kind = "floor";entry.art_id = "floor-"+id
	entry.remaining = null;entry.owned = id in state.floor_styles.owned;entry.description = "Floor pattern\nUnlimited painting"
	return entry
static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	# Lifecycle hook for an ended expedition, not an elapsed-time/manual reroll.
	if request.get("type")=="floor_refresh":
		var stock:Dictionary=state.floor_styles
		if not _integer(request.get("expected_rotation")) or request.expected_rotation!=stock.rotation:return {"ok":false,"reason":"stale_rotation"}
		stock.rotation=int(stock.rotation)+1;_choose(stock)
		return {"ok":true,"changed":true,"rotation":stock.rotation}
	if state.mode != "edit": return {"ok":false,"reason":"edit_required"}
	var data: Dictionary = state.floor_styles
	match request.get("type"):
		"floor_select":
			var id: Variant = request.get("style_id", "")
			if not id is String or (id != "" and id not in data.owned): return {"ok":false,"reason":"unowned_style"}
			if state.editor.layer != "floor": return {"ok":false,"reason":"floor_required"}
			state.editor.floor_brush = id;state.editor.selected_id = "";state.editor.belt_path = []
			return {"ok":true}
		"floor_purchase":
			if not _integer(request.get("expected_sequence")) or request.expected_sequence != data.purchase_sequence or request.get("rotation") != data.rotation: return {"ok":false,"reason":"stale_purchase"}
			if data.offer.is_empty() or request.get("offer_id") != "floor:"+str(data.offer): return {"ok":false,"reason":"unknown_offer"}
			if data.offer in data.owned: return {"ok":false,"reason":"already_owned"}
			var entry := style(data.offer)
			if int(state.coins) < int(entry.cost): return {"ok":false,"reason":"not_enough_coins"}
			state.coins = int(state.coins)-int(entry.cost)
			data.owned.push_front(data.offer);data.purchase_sequence = int(data.purchase_sequence)+1
			return {"ok":true,"offer_id":request.offer_id,"name":entry.name,"style_id":data.offer}
		"floor_paint":
			var brush: String = state.editor.get("floor_brush", "")
			if state.editor.layer != "floor" or brush.is_empty() or brush not in data.owned: return {"ok":false,"reason":"brush_required"}
			var cells: Variant = request.get("cells")
			if not cells is Array or cells.size()>4096: return {"ok":false,"reason":"invalid_cells"}
			# Validate the whole request before modifying any cell.
			for at in cells:
				if not at is Dictionary or not _integer(at.get("x")) or not _integer(at.get("y")) or at.x>=Expansion.columns(config.floor) or at.y<int(config.floor.get("backdrop_rows",0)) or at.y>=config.floor.rows: return {"ok":false,"reason":"invalid_cells"}
			var changed := false
			var blocked := false
			for at in cells:
				var cell := Vector2i(int(at.x),int(at.y))
				if Expansion.enabled(config.floor) and trash_at(state,config.floor,cell):
					blocked = true;continue
				var key := "%s,%s" % [cell.x,cell.y]
				if data.painted.get(key,"cream") == brush: continue
				if brush == "cream": data.painted.erase(key)
				else: data.painted[key] = brush
				changed = true
			return {"ok":true,"changed":changed,"blocked":blocked}
	return {"ok":false,"reason":"unknown_command"}
static func _integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value)>=0 and float(value)==floor(float(value)) and float(value)<=MAX_INTEGER
static func valid(config: Dictionary, state: Dictionary) -> bool:
	if not state.get("floor_styles") is Dictionary: return false
	var d: Dictionary = state.floor_styles
	if not d.get("owned") is Array or d.owned.is_empty() or d.owned[-1]!="cream" or d.owned.size()>definition().styles.size() or not d.get("painted") is Dictionary: return false
	if not _integer(d.get("purchase_sequence")) or int(d.purchase_sequence)!=d.owned.size()-1 or not _integer(d.get("seed")) or not _integer(d.get("rotation")): return false
	var seen: Dictionary = {}
	for id in d.owned:
		if not id is String or style(id).is_empty() or seen.has(id): return false
		seen[id] = true
	if not d.get("offer") is String or (d.offer!="" and (d.offer=="cream" or style(d.offer).is_empty())): return false
	for key in d.painted:
		if not key is String or d.painted[key] not in d.owned: return false
		var parts: PackedStringArray = key.split(",")
		if parts.size()!=2 or not parts[0].is_valid_int() or not parts[1].is_valid_int(): return false
		var x := int(parts[0]);var y := int(parts[1])
		if key!="%s,%s"%[x,y] or x<0 or x>=Expansion.columns(config.floor) or y<int(config.floor.get("backdrop_rows",0)) or y>=config.floor.rows: return false
	return true

static func trash_at(state: Dictionary, floor_data: Dictionary, cell: Vector2i) -> bool:
	if not Expansion.enabled(floor_data): return false
	for entry in Expansion.definition().patches:
		if entry.id not in state.get("expansion",{}).get("cleared",[]) and Expansion.contains(Expansion.patch(entry.id,floor_data),cell): return true
	return false

static func stroke_samples(start: Vector2, finish: Vector2) -> Array[float]:
	# Sample every crossed cell interior, including very short diagonal slivers.
	# Fixed-distance sampling can miss a tile when the stroke grazes its corner.
	var breaks: Array[float] = [0.0,1.0]
	var delta := finish-start
	for axis in range(2):
		if absf(delta[axis])<.0000001:continue
		for boundary in range(floori(minf(start[axis],finish[axis]))+1,ceili(maxf(start[axis],finish[axis]))):
			var t := (float(boundary)-start[axis])/delta[axis]
			if t>0 and t<1:breaks.append(t)
	breaks.sort()
	var result:Array[float]=[0.0,1.0]
	for i in range(breaks.size()-1):
		if breaks[i+1]-breaks[i]>.00000001:result.append((breaks[i]+breaks[i+1])*.5)
	return result
