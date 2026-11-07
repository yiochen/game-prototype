extends RefCounted
## Customers: one `customer` row per guest in the restaurant, keyed by id in
## arrival order. The visit lifecycle is the VISIT machine below; navigation
## (path search, movement, destination choice) is split out in
## features/navigation.gd. See docs/state-architecture.md.
const Machine = preload("res://scripts/engine/machine.gd")
const WORLD := "restaurant"

## Visit phases and the animation phases each allows. Transitions are driven
## by GameSession._step_customers; the definition validates stored states.
const VISIT := {"initial": "entrance_wait", "states": {
	"entrance_wait": {"visuals": ["stand"], "on": {"seat_assigned": "walking", "no_seat": "leaving"}},
	"walking": {"visuals": ["walk"], "on": {"arrived": "waiting", "arrived_with_meal": "eating", "seat_lost": "standing", "seat_unreachable": "leaving"}},
	"waiting": {"visuals": ["sit-down", "seated-wait"], "on": {"took_dish": "eating", "gave_up": "leaving", "seat_removed": "standing"}},
	"eating": {"visuals": ["eat"], "on": {"finished": "leaving", "seat_removed": "standing"}},
	"standing": {"visuals": ["stand", "walk"], "on": {"reseated": "waiting", "reseated_with_meal": "eating", "seat_found": "walking"}},
	"leaving": {"visuals": ["stand-up", "walk"], "on": {}},
}}

static func define(store) -> void:
	# Arrival order matters, so rows are saved in order. A guest's stool is a
	# reference: removing the stool stands the guest up through
	# GameSession._on_seat_removed.
	store.define_component("customer", {"owner": "customers", "durable": false, "ordered": true,
		"refs": {"seat_id": {"to": "layout", "on_delete": "notify"}}})

static func rows(store) -> Array:
	return store.table(WORLD, "customer").values()

static func extract(state: Dictionary, store) -> void:
	for customer in state.customers: store.set_row(WORLD, "customer", str(customer.id), customer)
	state.erase("customers")

static func hydrate(state: Dictionary, store) -> void:
	state.customers = rows(store).duplicate(true)

## Stools are first come, first served. A guest holds one while seated or on
## the way to it; a guest cut off from it (navigation wandering) leaves it free.
## The stool is the claim reference `seat_id`; who holds a stool is derived.
static func holds_seat(customer: Dictionary) -> bool:
	if customer.phase == "walking" and customer.get("navigation_mode") == "wander": return false
	return customer.phase != "leaving" or customer.visual_phase == "stand-up"

static func visuals(phase: String) -> Array:
	return VISIT.states.get(phase, {}).get("visuals", [])

static func is_phase(phase: Variant) -> bool:
	return VISIT.states.has(phase)
