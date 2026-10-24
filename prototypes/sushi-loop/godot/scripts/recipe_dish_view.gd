extends Control
const Art = preload("res://scripts/recipe_art.gd")
var recipe: Dictionary = {}
var unknown := false
func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
func _draw() -> void:
	Art.draw_dish(self, recipe, Rect2(Vector2.ZERO, size), unknown)
