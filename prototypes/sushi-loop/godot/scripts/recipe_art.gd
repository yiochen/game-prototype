extends RefCounted
## Same independent ImageGen plate/food layers in catalog, details and world.
const UISkin = preload("res://scripts/ui_skin.gd")
static var plates: Texture2D
static var food: Texture2D
static var heads: Dictionary = {}
static var photo_outer: Texture2D
static var photo_inner: Texture2D
static var stamp: Texture2D
static var calibration: Dictionary = {}
const TIERS := ["White", "Yellow", "Red", "Blue", "Black"]

static func head(identity: String) -> Texture2D:
	var id := identity.trim_prefix("chef-")
	if not id in ["lena", "omar", "ama", "mateo", "noor", "dalia", "ellis", "rowan"]: id = "lena"
	if not heads.has(id): heads[id] = load("res://assets/ui/chef-headshots/" + id + ".png")
	return heads[id]

static func draw_head(canvas: CanvasItem, identity: String, target: Rect2) -> void:
	var image := head(identity)
	canvas.draw_texture_rect(image, UISkin.fit_rect(image.get_size(), target), false)

static func _calibration() -> Dictionary:
	if calibration.is_empty(): calibration = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/recipes/manifest.json")).calibration
	return calibration

static func _rect(value: Array) -> Rect2:
	return Rect2(float(value[0]), float(value[1]), float(value[2]), float(value[3]))

static func draw_photo(canvas: CanvasItem, target: Rect2) -> void:
	if photo_outer == null: photo_outer = load("res://assets/ui/chef-headshots/photo-outer.png")
	var source := _rect(_calibration().photo_outer_source)
	canvas.draw_texture_rect_region(photo_outer, UISkin.fit_rect(source.size, target), source)

static func draw_photo_headshot(canvas: CanvasItem, identity: String, target: Rect2) -> void:
	if photo_inner == null: photo_inner = load("res://assets/ui/chef-headshots/photo-inner.png")
	var data := _calibration()
	var source := _rect(data.photo_inner_source)
	var face := UISkin.fit_rect(source.size, target)
	canvas.draw_texture_rect_region(photo_inner, face, source)
	var source_content := _rect(data.photo_inner_content)
	var scale_value := face.size.x/source.size.x
	var content := Rect2(face.position+(source_content.position-source.position)*scale_value, source_content.size*scale_value)
	var portrait := head(identity)
	var crop := Rect2(0,0,portrait.get_width(),portrait.get_width()*1.28)
	var destination := UISkin.fit_rect(crop.size, content)
	destination.position.y = content.end.y-destination.size.y
	canvas.draw_texture_rect_region(portrait,destination,crop)

static func plate_center(recipe: Dictionary) -> Vector2:
	var values: Array = _calibration().world_plate_anchors[str(recipe.get("tier","White"))].center
	return Vector2(float(values[0]),float(values[1]))

static func draw_dish(canvas: CanvasItem, recipe: Dictionary, target: Rect2, unknown := false, tint := Color.WHITE) -> void:
	if plates == null: plates = load("res://assets/ui/recipes/plates.png")
	if food == null: food = load("res://assets/ui/recipes/food.png")
	var square := UISkin.fit_rect(Vector2.ONE, target)
	var plate_cell := maxi(0, TIERS.find(str(recipe.get("tier", "White"))))
	_draw_cell(canvas, plates, plate_cell, square, tint)
	var food_target := Rect2(square.position + Vector2(square.size.x * 0.12, square.size.y * 0.01), square.size * 0.76)
	_draw_cell(canvas, food, 4 if unknown else int(recipe.get("food_cell", 2)), food_target, tint)

static func _draw_cell(canvas: CanvasItem, image: Texture2D, index: int, target: Rect2, tint: Color) -> void:
	var cell := image.get_size() / Vector2(3, 2)
	canvas.draw_texture_rect_region(image, target, Rect2(Vector2(index % 3, index / 3) * cell, cell), tint)

static func draw_assigned_stamp(canvas: CanvasItem, target: Rect2) -> void:
	if stamp == null: stamp = load("res://assets/ui/chef-headshots/assigned-stamp.png")
	var source := _rect(_calibration().assigned_stamp_source)
	canvas.draw_texture_rect_region(stamp,UISkin.fit_rect(source.size,target),source)

static func plate_visible_width(recipe: Dictionary) -> float:
	if plates == null: plates = load("res://assets/ui/recipes/plates.png")
	var bounds: Array = _calibration().world_plate_anchors[str(recipe.get("tier","White"))].bounds
	return (float(bounds[2])-float(bounds[0]))/(plates.get_width()/3.0)
