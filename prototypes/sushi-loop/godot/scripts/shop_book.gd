extends RefCounted
## Persistent supplies through the public command/save boundary. No clocks or RNG.
## Limited stock rotates once per ended expedition (#29): each limited offer
## restocks to its content quantity, except `once` goods already bought (the
## one tip jar per restaurant). `fresh` marks new stock until Shop is entered.
const PATH := "res://content/shop.json"
const MAX_INTEGER := 9007199254740991
static var _definition: Dictionary = {}

static func definition() -> Dictionary:
	if _definition.is_empty(): _definition = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return _definition

static func initialize(state: Dictionary) -> void:
	state.shop = {"purchase_sequence":0,"stock":{},"purchased":{},"rotation":0,"fresh":false}
	for offer in definition().offers:
		state.shop.stock[offer.id] = offer.stock
		state.shop.purchased[offer.inventory_id] = 0

static func snapshot(state: Dictionary) -> Dictionary:
	var offers: Array = definition().offers.duplicate(true)
	for offer in offers:
		offer.remaining = state.shop.stock[offer.id]
		offer.erase("stock")
	return {"purchase_sequence":int(state.shop.purchase_sequence),"offers":offers,"rotation":int(state.shop.rotation),"fresh":bool(state.shop.fresh)}

## The ended expedition's one restock. Callers hold the run's end transition,
## which happens once per run, so a replay cannot rotate twice.
static func rotate(state: Dictionary) -> void:
	var shop: Dictionary = state.shop
	for offer in definition().offers:
		if offer.stock == null: continue
		var owned := int(shop.purchased[offer.inventory_id])
		shop.stock[offer.id] = 0 if offer.get("once", false) and owned > 0 else int(offer.stock)
	shop.rotation = int(shop.rotation) + 1
	shop.fresh = true

## Entering Shop clears the new-stock dot.
static func seen(state: Dictionary) -> Dictionary:
	if not state.shop.fresh: return {"ok":true,"changed":false}
	state.shop.fresh = false
	return {"ok":true,"changed":true}

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
	if not _integer(shop.get("rotation")) or not shop.get("fresh") is bool: return false
	if shop.stock.size() != definition().offers.size() or shop.purchased.size() != definition().offers.size(): return false
	var total := 0
	for offer in definition().offers:
		if not shop.stock.has(offer.id) or not _integer(shop.purchased.get(offer.inventory_id)): return false
		var count := int(shop.purchased[offer.inventory_id])
		if count > MAX_INTEGER-total: return false
		total += count
		if offer.stock == null:
			if shop.stock[offer.id] != null: return false
		elif not _integer(shop.stock[offer.id]) or int(shop.stock[offer.id]) > int(offer.stock): return false
		# Before any rotation, stock is exactly what purchases left.
		elif int(shop.rotation) == 0 and int(shop.stock[offer.id]) + count != int(offer.stock): return false
		elif offer.get("once", false) and int(shop.stock[offer.id]) + count > int(offer.stock): return false
	return total == int(shop.purchase_sequence)

static func normalize(state: Dictionary) -> void:
	state.shop.purchase_sequence = int(state.shop.purchase_sequence)
	state.shop.rotation = int(state.shop.rotation)
	for id in state.shop.purchased: state.shop.purchased[id] = int(state.shop.purchased[id])
	for id in state.shop.stock:
		if state.shop.stock[id] != null: state.shop.stock[id] = int(state.shop.stock[id])

static func _integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER

## Saves made before an offer existed gain its full stock and no purchases.
static func add_missing_offers(shop: Variant) -> Variant:
	if not shop is Dictionary or not shop.get("stock") is Dictionary or not shop.get("purchased") is Dictionary: return shop
	for offer in definition().offers:
		if not shop.stock.has(offer.id): shop.stock[offer.id] = offer.stock
		if not shop.purchased.has(offer.inventory_id): shop.purchased[offer.inventory_id] = 0
	return shop

## Saves made before stock rotation (#29) have never rotated.
static func add_rotation(shop: Variant) -> Variant:
	if not shop is Dictionary: return shop
	if not shop.has("rotation"): shop.rotation = 0
	if not shop.has("fresh"): shop.fresh = false
	return shop
