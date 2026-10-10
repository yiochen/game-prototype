extends RefCounted
## Shared type treatment for the restaurant, controls and component gallery.

static func body() -> Font:
	var font := FontVariation.new()
	font.base_font = load("res://assets/fonts/Nunito.ttf")
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 650}
	return font

static func heading() -> Font:
	return load("res://assets/fonts/Delius.ttf")
