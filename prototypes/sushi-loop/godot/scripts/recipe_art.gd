extends RefCounted
## Same independent ImageGen plate/food layers in catalog, details and world.
const UISkin = preload("res://scripts/ui_skin.gd")
static var plates: Texture2D
static var food: Texture2D
static var heads: Dictionary = {}
static var photo: Texture2D
const TIERS := ["White", "Yellow", "Red", "Blue", "Black"]

static func head(identity: String) -> Texture2D:
	var id := identity.trim_prefix("chef-")
	if not id in ["lena", "omar", "ama", "mateo", "noor", "dalia", "ellis", "rowan"]: id = "lena"
	if not heads.has(id): heads[id] = load("res://assets/ui/chef-headshots/" + id + ".png")
	return heads[id]

static func draw_head(canvas: CanvasItem, identity: String, target: Rect2) -> void:
	var image := head(identity)
	canvas.draw_texture_rect(image, UISkin.fit_rect(image.get_size(), target), false)

static func draw_photo(canvas: CanvasItem, target: Rect2) -> void:
	if photo == null: photo = load("res://assets/ui/chef-headshots/instant-photo.png")
	var source := Rect2(128, 104, 980, 1110)
	canvas.draw_texture_rect_region(photo, UISkin.fit_rect(source.size, target), source)

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
