extends Control
## Rolling-digit presentation of a Label (#61). The Label keeps its layout,
## compact formatting and accessibility; this control draws the same caption on
## top and rolls each changed character: up when the value rises, down when it
## falls, lower digits first, with a short scale pulse. Approved composition:
## design/cash-preview/ (HUD & sale pop).

const ROLL_SECONDS := 0.34
const STAGGER_SECONDS := 0.035
const PULSE_SECONDS := 0.42
const RISE := Color("238a4b")
const FALL := Color("c8452e")

var source: Label
var reduced_motion := false
var _shown := ""
var _previous := ""
var _rising := true
var _changed_at := -1.0
var _clock := 0.0

func _init(label: Label) -> void:
	source = label
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = false

func _process(delta: float) -> void:
	_clock += delta
	if source == null: return
	position = source.position
	size = source.size
	pivot_offset = Vector2(0, size.y * 0.5)
	var text := source.text
	if text != _shown:
		_previous = _shown
		_rising = _numeric(text) >= _numeric(_shown)
		_shown = text
		_changed_at = -1.0 if reduced_motion or _previous.is_empty() else _clock
	var age := _clock - _changed_at
	var pulse := 0.0 if _changed_at < 0.0 or age >= PULSE_SECONDS else sin(PI * age / PULSE_SECONDS)
	scale = Vector2.ONE * (1.0 + pulse * (0.22 if _rising else 0.12))
	queue_redraw()

func _numeric(text: String) -> float:
	return float(text) if text.is_valid_float() else 0.0

func _draw() -> void:
	if source == null or _shown.is_empty(): return
	var font: Font = source.get_theme_font("font")
	var size_px: int = source.get_theme_font_size("font_size")
	var ink: Color = source.get_theme_color("font_color")
	var age := _clock - _changed_at
	if _changed_at >= 0.0 and age < PULSE_SECONDS:
		ink = ink.lerp(RISE if _rising else FALL, sin(PI * age / PULSE_SECONDS))
	var ascent := font.get_ascent(size_px)
	var baseline := (size.y - font.get_height(size_px)) * 0.5 + ascent
	var line := font.get_height(size_px)
	# Right-align old and new captions so units, tens and so on line up.
	var new_width := font.get_string_size(_shown, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px).x
	var left := 0.0 if source.horizontal_alignment == HORIZONTAL_ALIGNMENT_LEFT else (size.x - new_width) * 0.5
	var right := left + new_width
	var old := _previous.lpad(_shown.length()) if _previous.length() < _shown.length() else _previous.right(_shown.length())
	var x := right
	for index in range(_shown.length() - 1, -1, -1):
		var glyph := _shown[index]
		var width := font.get_string_size(glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px).x
		x -= width
		var place := _shown.length() - 1 - index
		var t := 1.0
		if _changed_at >= 0.0 and old[index] != glyph:
			t = clampf((age - place * STAGGER_SECONDS) / ROLL_SECONDS, 0.0, 1.0)
			t = 1.0 - pow(1.0 - t, 3.0)
		var direction := -1.0 if _rising else 1.0
		if t < 1.0:
			var clip := Rect2(Vector2(x - 2, baseline - ascent - 2), Vector2(width + 4, line + 4))
			_glyph(font, old[index], Vector2(x, baseline + direction * line * t), size_px, ink, clip)
			_glyph(font, glyph, Vector2(x, baseline - direction * line * (1.0 - t)), size_px, ink, clip)
		else:
			draw_string(font, Vector2(x, baseline), glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, ink)

## A glyph faded as it leaves its digit window, so a roll reads as a reel.
func _glyph(font: Font, glyph: String, at: Vector2, size_px: int, ink: Color, window: Rect2) -> void:
	if glyph.strip_edges().is_empty(): return
	var offset := absf(at.y - (window.position.y + font.get_ascent(size_px) + 2)) / window.size.y
	draw_string(font, at, glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, Color(ink, ink.a * clampf(1.0 - offset * 1.4, 0.0, 1.0)))
