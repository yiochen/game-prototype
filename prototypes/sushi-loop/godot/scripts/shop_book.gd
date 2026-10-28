extends RefCounted
## Persistent supplies through the public command/save boundary. No clocks or RNG.
const PATH := "res://content/shop.json"
const MAX_INTEGER := 9007199254740991
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func initialize(state: Dictionary) -> void:
	state.shop = {"purchase_sequence":0,"stock":{},"purchased":{}}
	for offer in definition().offers:
		state.shop.stock[offer.id] = offer.stock
		state.shop.purchased[offer.inventory_id] = 0

static func snapshot(state: Dictionary) -> Dictionary:
	var offers: Array = definition().offers.duplicate(true)
	for offer in offers:
		offer.remaining = state.shop.stock[offer.id]
		offer.erase("stock")
	return {"purchase_sequence":int(state.shop.purchase_sequence),"offers":offers}

static func command(state: Dictionary, request: Dictionary) -> Dictionary:
	if state.mode != "edit": return {"ok":false,"reason":"edit_required"}
	if not _integer(request.get("expected_sequence")) or request.expected_sequence != state.shop.purchase_sequence:
		return {"ok":false,"reason":"stale_purchase"}
	var offer: Dictionary = {}
	for candidate in definition().offers:
		if candidate.id == request.get("offer_id"): offer = candidate
	if offer.is_empty(): return {"ok":false,"reason":"unknown_offer"}
	var remaining: Variant = state.shop.stock[offer.id]
	if remaining != null and int(remaining) == 0: return {"ok":false,"reason":"sold_out"}
	if int(state.coins) < int(offer.cost): return {"ok":false,"reason":"not_enough_coins"}
	var stock: Dictionary = {}
	for entry in state.inventory:
		if entry.id == offer.inventory_id: stock = entry
	if stock.is_empty(): return {"ok":false,"reason":"unknown_inventory"}
	if int(stock.count) >= MAX_INTEGER or int(state.shop.purchase_sequence) >= MAX_INTEGER:
		return {"ok":false,"reason":"inventory_full"}
	state.coins = int(state.coins) - int(offer.cost)
	stock.count = int(stock.count) + 1
	state.shop.purchased[offer.inventory_id] = int(state.shop.purchased[offer.inventory_id]) + 1
	state.shop.purchase_sequence = int(state.shop.purchase_sequence) + 1
	if remaining != null: state.shop.stock[offer.id] = int(remaining) - 1
	return {"ok":true,"offer_id":offer.id,"inventory_id":offer.inventory_id,"cost":int(offer.cost),"purchase_sequence":int(state.shop.purchase_sequence)}

static func valid(state: Dictionary) -> bool:
	if not state.get("shop") is Dictionary: return false
	var shop: Dictionary = state.shop
	if not _integer(shop.get("purchase_sequence")) or not shop.get("stock") is Dictionary or not shop.get("purchased") is Dictionary: return false
	if shop.stock.size() != definition().offers.size() or shop.purchased.size() != definition().offers.size(): return false
	var total := 0
	for offer in definition().offers:
		if not shop.stock.has(offer.id) or not _integer(shop.purchased.get(offer.inventory_id)): return false
		var count := int(shop.purchased[offer.inventory_id])
		if count > MAX_INTEGER-total: return false
		total += count
		if offer.stock == null:
			if shop.stock[offer.id] != null: return false
		elif not _integer(shop.stock[offer.id]) or int(shop.stock[offer.id]) + count != int(offer.stock): return false
	return total == int(shop.purchase_sequence)

static func normalize(state: Dictionary) -> void:
	state.shop.purchase_sequence = int(state.shop.purchase_sequence)
	for id in state.shop.purchased: state.shop.purchased[id] = int(state.shop.purchased[id])
	for id in state.shop.stock:
		if state.shop.stock[id] != null: state.shop.stock[id] = int(state.shop.stock[id])

static func _integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER
