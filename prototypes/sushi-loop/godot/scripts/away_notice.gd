extends Control
## The automatic while-away cue (#29): a cash icon and "+420 while away" in the
## reserved line under the balance. It fades in, holds, and fades out on its
## own, never takes input and never moves neighbouring HUD controls. Reduced
## motion shows and hides it without fading or sliding.

const INK := Color("233d58")
const GAIN := Color("17673a")
const FADE_SECONDS := 0.3

var reduced_motion := false
var hold_seconds := 3.6
var icon := TextureRect.new()
var label := Label.new()
var _age := INF

func _init(cash_icon: Texture2D, font: Font) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.texture = cash_icon
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(icon)
	label.add_theme_font_override("font", font)
	label.add_theme_color_override("font_color", GAIN)
	label.add_theme_color_override("font_outline_color", Color("fff3db"))
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.accessibility_live = AccessibilityServer.LIVE_POLITE
	add_child(label)
	hide()

## Shows a positive credit; zero income is never announced.
func present(amount: int) -> void:
	if amount <= 0: return
	label.text = "+%d while away" % amount
	label.accessibility_name = "%d coins earned while away" % amount
	_age = 0.0
	show()

func showing() -> bool:
	return visible

## The reserved line: icon at the left, caption after it, at the HUD unit.
func place(line: Rect2, unit: float) -> void:
	position = line.position
	size = line.size
	var side := minf(line.size.y, 40 * unit)
	icon.position = Vector2(0, (line.size.y - side) * 0.5)
	icon.size = Vector2(side * 1.4, side)
	label.add_theme_font_size_override("font_size", maxi(8, int(30 * unit)))
	label.add_theme_constant_override("outline_size", maxi(1, int(10 * unit)))
	label.position = Vector2(side * 1.4 + 8 * unit, 0)
	label.size = Vector2(maxf(0.0, line.size.x - label.position.x), line.size.y)

func _process(delta: float) -> void:
	if not visible: return
	_age += delta
	var total := hold_seconds + FADE_SECONDS * 2.0
	if _age >= total:
		hide()
		return
	if reduced_motion:
		modulate.a = 1.0
		return
	var fade_in := clampf(_age / FADE_SECONDS, 0.0, 1.0)
	var fade_out := clampf((total - _age) / FADE_SECONDS, 0.0, 1.0)
	modulate.a = minf(fade_in, fade_out)
	# A short rise into place as it appears.
	label.position.y = (1.0 - fade_in) * 10.0
