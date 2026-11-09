extends Panel
## The game's one red "something new here" dot: Workshop tabs (through
## GameButton.dot), and Edit and Shop for rotated Shop stock (#29).
## Decorative only; the owning control carries the accessible state.
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const COLOR := Color("ff5f48")

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

## Inside the top-right corner of a face `face_width` wide with corner `radius`.
func place(face_width: float, radius: float, unit: float) -> void:
	size = Vector2.ONE * 18 * unit
	position = Vector2(face_width - minf(radius, 36 * unit) - 2 * unit, 14 * unit)
	add_theme_stylebox_override("panel", PopupSkin.flat(COLOR, 9 * unit))
