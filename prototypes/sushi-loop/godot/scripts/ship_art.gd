extends RefCounted
## The yellow submarine (#28 r3+): ImageGen parts, every part always fitted.
## Hull and paired side collectors swap their whole sprite at each look tier
## (WorkshopBook.tier); the Harpoon track changes the fired harpoon instead
## (harpoon_art.gd), so nothing weapon-like is mounted on the hull. Parts are
## composed in one shared frame centred on the hull, the collision centre, so
## any tier mix keeps the same footprint. Anchors and compose constants are
## baked by design/workshop-preview/tools/bake_native.py (layout.json); the
## dock variants carry the approved cyan interactable outline.
const DIR := "res://assets/workshop/"
static var _layout: Dictionary = {}
static var _textures: Dictionary = {}

static func layout() -> Dictionary:
	if _layout.is_empty(): _layout = JSON.parse_string(FileAccess.get_file_as_string(DIR + "layout.json"))
	return _layout

static func texture(path: String) -> Texture2D:
	if not _textures.has(path): _textures[path] = load(DIR + path)
	return _textures[path]

static func tiers_of(gear_tiers: Dictionary) -> Vector2i:
	return Vector2i(clampi(int(gear_tiers.get("hull", 1)), 1, 3), clampi(int(gear_tiers.get("collector", 1)), 1, 3))

## Layers (texture, rect in part pixels relative to the hull centre, flip) for a tier mix.
static func layers(gear_tiers: Dictionary) -> Array:
	var t := tiers_of(gear_tiers)
	var data := layout()
	var hull: Dictionary = data.hull[t.x - 1]
	var col: Dictionary = data.collector[t.y - 1]
	var cs := float(data.collector_scale)
	var ov := float(data.collector_overlap)
	var hx := -float(hull.size[0]) / 2.0
	var hy := -float(hull.size[1]) / 2.0
	var cw := float(col.size[0]) * cs
	var ch := float(col.size[1]) * cs
	var ly := float(hull.left[1]) + hy - float(col.bracket[1]) * cs
	var collector := texture("parts/collector-%d.png" % t.y)
	return [
		[collector, Rect2(float(hull.left[0]) + hx + ov - float(col.bracket[0]) * cs, ly, cw, ch), false],
		[collector, Rect2(float(hull.right[0]) + hx - ov + (float(col.bracket[0]) - float(col.size[0])) * cs, ly, cw, ch), true],
		[texture("parts/hull-%d.png" % t.x), Rect2(hx, hy, float(hull.size[0]), float(hull.size[1])), false],
	]

## Draw the ship with its hull centred at `centre` and the hull `hull_px` tall.
static func draw(canvas: CanvasItem, centre: Vector2, hull_px: float, gear_tiers: Dictionary, modulate := Color.WHITE) -> void:
	var s := hull_px / float(layout().hull_height)
	for layer in layers(gear_tiers):
		var r: Rect2 = layer[1]
		var rect := Rect2(centre + r.position * s, r.size * s)
		# A negative width mirrors the texture in place (Godot keeps the rect's span).
		if layer[2]: rect.size.x = -rect.size.x
		canvas.draw_texture_rect(layer[0], rect, false, modulate)

## The hull's nose hatch (where the harpoon leaves), relative to the hull centre.
static func nose_offset(hull_px: float, gear_tiers: Dictionary) -> Vector2:
	var t := tiers_of(gear_tiers)
	var hull: Dictionary = layout().hull[t.x - 1]
	var s := hull_px / float(layout().hull_height)
	return (Vector2(float(hull.nose[0]), float(hull.nose[1])) - Vector2(float(hull.size[0]), float(hull.size[1])) / 2.0) * s

## The outlined dock ship (interactable) and where it draws: [texture, rect].
static func dock(centre: Vector2, hull_px: float, gear_tiers: Dictionary) -> Array:
	var t := tiers_of(gear_tiers)
	var tex := texture("dock/ship-%d-%d.png" % [t.x, t.y])
	var data: Dictionary = layout().dock
	var s := hull_px / float(data.hull_height)
	var origin := centre - Vector2(float(data.hull_centre[0]), float(data.hull_centre[1])) * s
	return [tex, Rect2(origin, Vector2(tex.get_width(), tex.get_height()) * s)]

static func draw_dock(canvas: CanvasItem, centre: Vector2, hull_px: float, gear_tiers: Dictionary, modulate := Color.WHITE) -> void:
	var placed := dock(centre, hull_px, gear_tiers)
	canvas.draw_texture_rect(placed[0], placed[1], false, modulate)

## Size of the composed ship box (part pixels) for a given hull height.
static func frame_size(hull_px: float) -> Vector2:
	var f: Array = layout().frame
	return Vector2(float(f[2]), float(f[3])) * hull_px / float(layout().hull_height)
