extends RefCounted
## Layout: every placed object (chef position, belt tile, seat, decor) is one
## `layout` row keyed by id, in placement order. Belt routing and the dish on a
## tile are still part of the belt's row; splitting them into their own tables
## is listed as follow-up in docs/state-architecture.md. The inventory and the
## editor's selection, paging and belt path are layout slices.
const WORLD := "restaurant"

static func define(store) -> void:
	# Removing a belt clears every link to it. Chef stations and seat claims
	# refer to layout rows by id as well; their owners handle those removals.
	# Placement order decides junction inputs, so rows are saved in order.
	store.define_component("layout", {"owner": "layout", "ordered": true, "refs": {"next_id": {"to": "layout", "on_delete": "clear"}}})

## Live rows in placement order; the order decides junction inputs.
static func rows(store) -> Array:
	return store.table(WORLD, "layout").values()

static func extract(state: Dictionary, store) -> void:
	for object in state.objects: store.set_row(WORLD, "layout", str(object.id), object)
	state.erase("objects")

## The single-dictionary form, for saves and for validators not yet moved.
static func hydrate(state: Dictionary, store) -> void:
	state.objects = rows(store).duplicate(true)
