extends Button
## The game's one button widget for popups, sheets and full-screen rooms.
## Attributes, not separate implementations, choose its look:
##   tone      PRIMARY (vermilion, the important action), SECONDARY (cream),
##             MAPLE (wood-grain tabs and price buttons), WALNUT (Shop action)
##   selected  a toggle tab that is the current one (cream, no grain)
##   disabled  muted parchment with no grain
##   verb/cost a price button: a small verb line over a currency icon and amount
##   short     what the player has, shown as "have / cost" with the cost in red
##   glyph     an icon before the caption
##   dot       a red "something new here" dot in the top-right corner
## The face sinks onto its lip from pointer down. The native hit target never
## moves, keeps at least 44 physical px, and shows the shared focus ring.
## Call `fit(unit, physical)` after giving it a size; attributes restyle it.
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Typography = preload("res://scripts/typography.gd")
enum Tone { PRIMARY, SECONDARY, MAPLE, WALNUT, LINK }
const LIP := 4.0
const PALETTE := {
	Tone.PRIMARY: {"face": Color("ff624b"), "edge": Color("f2553c"), "lip": Color("bd4528"), "ink": Color("fff9ed")},
	Tone.SECONDARY: {"face": Color("fff1d5"), "edge": Color("ecd2a6"), "lip": Color("b98450"), "ink": Color("633b21")},
	Tone.MAPLE: {"face": Color("f2c88a"), "edge": Color("b7783a"), "lip": Color("a16635"), "ink": Color("643816")},
	Tone.WALNUT: {"face": Color("8f4320"), "edge": Color("6e3016"), "lip": Color("5c2a12"), "ink": Color("fff1d3")},
	# A bare text action for destructive choices (Fire…): no surface, red ink.
	Tone.LINK: {"face": Color.TRANSPARENT, "edge": Color.TRANSPARENT, "lip": Color.TRANSPARENT, "ink": Color("ad4835")},
}
const SHORT := Color("b84432")
const SELECTED := {"face": Color("fff1d3"), "edge": Color("e1bc85"), "lip": Color("c9925a"), "ink": Color("592c10")}
const DISABLED := {"face": Color("e8d8b9"), "edge": Color("c9b595"), "lip": Color("baa486"), "ink": Color("806b52")}
const DOT := Color("ff5f48")
static var _grain: Texture2D

var tone := Tone.SECONDARY: set = _set_tone
var selected := false: set = _set_selected
var dot := false: set = _set_dot
var verb := "": set = _set_verb
var cost := "": set = _set_cost
var cost_icon: Texture2D: set = _set_cost_icon
var short := "": set = _set_short
var glyph: Texture2D: set = _set_glyph
var captioned := true  # false: the text is only the accessible/test label (a bare price)
var caption_px := 28.0
var radius := 26.0
var unit := 1.0
var _physical := 1.0
var _down := false
var _state := ""
var visual: Control
var surface: Panel
var grain: TextureRect
var caption: Label
var verb_label: Label
var cost_label: Label
var have_label: Label
var cost_image: TextureRect
var glyph_image: TextureRect
var dot_panel: Panel

func _init() -> void:
	var font := Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 850}
	add_theme_font_override("font", font)
	# The Button keeps its text for accessibility; the visible caption is a label above the grain.
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color", "font_disabled_color"]:
		add_theme_color_override(key, Color.TRANSPARENT)
	for treatment in ["normal", "hover", "pressed", "hover_pressed", "disabled"]: add_theme_stylebox_override(treatment, StyleBoxEmpty.new())
	visual = Control.new(); visual.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(visual)
	surface = Panel.new(); surface.mouse_filter = Control.MOUSE_FILTER_IGNORE; visual.add_child(surface)
	grain = grain_face(visual)
	glyph_image = _image(); caption = _label(font); verb_label = _label(font); cost_image = _image(); have_label = _label(font); cost_label = _label(font)
	dot_panel = Panel.new(); dot_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE; visual.add_child(dot_panel)
	button_down.connect(func(): _down = true; restyle())
	button_up.connect(func(): _down = false; restyle())
	focus_entered.connect(restyle); focus_exited.connect(restyle)
	toggled.connect(func(_on): restyle())
	resized.connect(restyle)

func _image() -> TextureRect:
	var image := TextureRect.new(); image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	visual.add_child(image); return image

func _label(font: Font) -> Label:
	var label := Label.new(); label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_override("font", font); label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	visual.add_child(label); return label

## Scale with the screen's design unit; `physical` keeps the 44 px touch minimum.
func fit(scale_unit: float, physical := 1.0) -> void:
	unit = scale_unit; _physical = maxf(.001, physical)
	custom_minimum_size = Vector2.ONE * 44.01 / _physical
	restyle()

## Show or clear the held face for presses a screen routes itself (a
## scrolling catalog's touch); `release()` cancels without activating.
func hold(on: bool) -> void:
	_down = on; restyle()

func release() -> void: hold(false)

func colors() -> Dictionary:
	if disabled and tone == Tone.LINK: return {"face": Color.TRANSPARENT, "edge": Color.TRANSPARENT, "lip": Color.TRANSPARENT, "ink": DISABLED.ink}
	if disabled: return DISABLED
	if selected: return SELECTED
	return PALETTE[tone]

func is_held() -> bool: return _down and not disabled

func _draw() -> void:
	# Disabled and other Button-side changes arrive as redraws; restyle once per change.
	if _key() != _state: call_deferred("restyle")

func _key() -> String: return "%s|%s|%s|%s|%s" % [disabled, selected, _down, has_focus(), text]

func restyle() -> void:
	if visual == null: return
	_state = _key()
	var c := colors()
	var held := is_held()
	var r := minf(radius, size.y / unit * .5) * unit
	visual.position = Vector2(0, (LIP - 1.0) * unit if held else 0.0); visual.size = size
	surface.position = Vector2.ZERO; surface.size = size - Vector2(0, LIP * unit)
	surface.add_theme_stylebox_override("panel", face_style(c, r, unit, held, tone == Tone.MAPLE))
	grain.visible = tone == Tone.MAPLE and not selected and not disabled
	layout_grain(grain, surface.size, r, unit, held)
	add_theme_stylebox_override("focus", PopupSkin.focus_ring(r, unit))
	_layout_content(c.ink)
	dot_panel.visible = dot
	dot_panel.size = Vector2.ONE * 18 * unit
	dot_panel.position = Vector2(surface.size.x - minf(r, 36 * unit) - 2 * unit, 14 * unit)
	dot_panel.add_theme_stylebox_override("panel", PopupSkin.flat(DOT, 9 * unit))

## The shared face: colour, edge and the lip it sinks onto. Also used by the
## Edit dock's tabs, which keep the editor's native button plumbing.
static func face_style(c: Dictionary, r: float, scale_unit: float, held: bool, grained := false) -> StyleBoxFlat:
	var style := PopupSkin.flat(c.face.darkened(.06) if held and not grained else c.face, r)
	style.border_color = c.edge; style.set_border_width_all(maxi(1, int(2 * scale_unit)))
	style.shadow_color = c.lip; style.shadow_size = maxi(1, int(scale_unit)); style.shadow_offset = Vector2(0, 1.0 if held else LIP) * scale_unit
	return style

static func grain_face(parent: Control) -> TextureRect:
	if _grain == null: _grain = load("res://assets/ui/wood-editor/wood-grain.png")
	return PopupSkin.make_face(parent, _grain)

static func layout_grain(face: TextureRect, face_size: Vector2, r: float, scale_unit: float, held := false) -> void:
	face.position = Vector2.ONE * 2 * scale_unit
	PopupSkin.layout_face(face, face_size - Vector2.ONE * 4 * scale_unit, scale_unit)
	face.material.set_shader_parameter("corner_radius", maxf(0, r - 2 * scale_unit))
	face.modulate = Color(.93, .93, .93) if held else Color.WHITE

func _layout_content(ink: Color) -> void:
	var face := Rect2(Vector2.ZERO, surface.size)
	var font: Font = caption.get_theme_font("font")
	var px := maxi(1, int(caption_px * unit))
	var priced := cost != ""
	var stacked := priced and verb != ""
	caption.text = text; caption.visible = captioned and text != "" and not stacked
	caption.add_theme_font_size_override("font_size", px); caption.add_theme_color_override("font_color", ink)
	glyph_image.visible = glyph != null and not priced
	glyph_image.texture = glyph; glyph_image.modulate = ink
	verb_label.visible = stacked; cost_label.visible = priced; cost_image.visible = priced and cost_icon != null
	cost_label.text = cost; cost_label.add_theme_color_override("font_color", SHORT if short != "" else ink)
	have_label.visible = priced and short != ""; have_label.text = short + " / "; have_label.add_theme_color_override("font_color", ink)
	cost_image.texture = cost_icon; cost_image.modulate = Color(1, 1, 1, .55) if disabled else Color.WHITE
	if stacked:
		# Price button: a small verb over the currency icon and amount.
		var verb_px := maxi(1, int(21 * unit))
		verb_label.text = verb; verb_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		verb_label.add_theme_font_size_override("font_size", verb_px)
		verb_label.add_theme_color_override("font_color", ink.lerp(Color("c49a6c"), .35) if not disabled else ink)
		var verb_h := verb_px * 1.3
		var top := (face.size.y - verb_h - px * 1.3) * .5
		verb_label.position = Vector2(0, top); verb_label.size = Vector2(face.size.x, verb_h)
		_row(face, top + verb_h, px * 1.3, px, [[cost_image, px * 1.25, px * .2], [cost_label, _width(font, cost, px), 0.0]])
		return
	# One line: [glyph] caption [currency amount].
	var parts := []
	if glyph_image.visible: parts.append([glyph_image, px * 1.05, px * .3])
	if caption.visible: parts.append([caption, _width(font, text, px), px * .45 if priced else 0.0])
	if cost_image.visible: parts.append([cost_image, px * 1.2, px * .25])
	if have_label.visible: parts.append([have_label, _width(font, have_label.text, px), 0.0])
	if priced: parts.append([cost_label, _width(font, cost, px), 0.0])
	cost_label.add_theme_font_size_override("font_size", px)
	_row(face, 0.0, face.size.y, px, parts)

func _width(font: Font, value: String, px: int) -> float:
	return font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, px).x

## Centre `parts` ([node, width, gap after]) on one line of height `h` at `top`.
func _row(face: Rect2, top: float, h: float, px: int, parts: Array) -> void:
	var total := 0.0
	for i in range(parts.size()): total += parts[i][1] + (parts[i][2] if i < parts.size() - 1 else 0.0)
	var x := (face.size.x - total) * .5
	for part in parts:
		var node: Control = part[0]
		if node is Label:
			node.add_theme_font_size_override("font_size", px)
			node.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
			node.position = Vector2(x, top); node.size = Vector2(part[1] + 2, h)
		else:
			node.position = Vector2(x, top + (h - px * 1.1) * .5); node.size = Vector2(part[1], px * 1.1)
		x += part[1] + part[2]

func _set_tone(value: Tone) -> void: tone = value; restyle()
func _set_selected(value: bool) -> void: selected = value; restyle()
func _set_dot(value: bool) -> void: dot = value; restyle()
func _set_verb(value: String) -> void: verb = value; restyle()
func _set_cost(value: String) -> void: cost = value; restyle()
func _set_cost_icon(value: Texture2D) -> void: cost_icon = value; restyle()
func _set_short(value: String) -> void: short = value; restyle()
func _set_glyph(value: Texture2D) -> void: glyph = value; restyle()
