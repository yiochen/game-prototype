extends Control
## Workshop (#28), the approved full-screen room from design/workshop-preview/,
## shared by gameplay and --workshop-gallery. The ImageGen room is anchored to
## the top and cover-fitted (capped on wide windows over a dimmed copy); the
## cradle and ship sit in whatever floor is free between the wall and the card
## tray, so any portrait shape works. The doorway (tagged "Sushi Bar"), Escape
## and Back leave. The tray holds the game's one tab control (Equipment |
## Power-ups) over the beige catalog. Upgrade pays one level and stays here;
## unaffordable buttons are disabled with no shortage message; capped tracks
## keep their card with a MAX stamp. Power-up cards say what they do and which
## way the next level moves it (no internal units). Tapping the ship test-fires
## the current harpoon; a Harpoon upgrade test-fires the new one.
const WorkshopBook = preload("res://scripts/workshop_book.gd")
const ShipArt = preload("res://scripts/ship_art.gd")
const Harpoon = preload("res://scripts/expedition/harpoon_art.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const GameButton = preload("res://scripts/game_button.gd")
const INK := Color("592c10")
const MUTED := Color("866347")
const TEAL := Color("17675f")
const CREAM := Color("fff1d3")
const ROOM_SIZE := Vector2(853, 1844)
const CRADLE_ASPECT := 560.0 / 822.0
## Player-facing copy. Names and what each track does; never internal units.
const COPY := {
	"hull": {"name": "Hull", "stat": "Maximum hull"},
	"harpoon": {"name": "Harpoon", "stat": "Reeling strength"},
	"collector": {"name": "Collector", "stat": "Attraction range"},
	"shield": {"name": "Shield", "does": "Shield pickups block rock hits", "better": "Lasts longer"},
	"passage": {"name": "Passage", "does": "Portals carry you through a salvage current", "better": "Longer ride"},
	"launch": {"name": "Shield at start", "does": "Begin each dive already shielded", "better": "Lasts longer", "unlock": "Unlock"},
}
const GROUPS := [["equipment", "Equipment"], ["powerup", "Power-ups"]]
signal upgrade_requested(request: Dictionary)
signal close_requested(from: Vector2)

var wood = Wood.new()
var font: Font
var heavy: Font
var state: Dictionary = {}
var area := Rect2()
var safe_top := 0.0
var unit := 1.0
var reduced_motion := false
var interaction_blocked := false
var gallery := false
var group := "equipment"
var focused_before: Control
var room_rect := Rect2()

var room: Control
var sign_label: Label
var door: Button
var door_tag: Panel
var door_label: Label
var hero: Button
var cradle: TextureRect
var ship: ShipCanvas
var salvage_pill: Panel
var salvage_icon: TextureRect
var salvage_label: Label
var tray: Panel
var tray_face: TextureRect
var tabs: Array[Button] = []
var catalog_shade: ColorRect
var catalog_backing: Panel
var catalog: ScrollContainer
var content: VBoxContainer
var rows: Dictionary = {}
var _signature := ""

## Room art: cover-fitted room, plus a dimmed copy behind it on wide windows.
class RoomArt extends Control:
	var texture: Texture2D
	var rect := Rect2()
	func _draw() -> void:
		if rect.size.x < size.x - .5:
			var scale := maxf(size.x / ROOM_SIZE.x, size.y / ROOM_SIZE.y)
			draw_texture_rect(texture, Rect2((size - ROOM_SIZE * scale) * .5, ROOM_SIZE * scale), false, Color(.62, .58, .55))
		draw_texture_rect(texture, rect, false)

## The ship on its cradle, the test-fire harpoon and new-look sparkles.
class ShipCanvas extends Control:
	var tiers: Dictionary = {}
	var hull_px := 100.0
	var centre := Vector2.ZERO
	var harpoon_tier := 1
	var fire_t := -1.0
	var sparks: Array = []
	var reduced := false
	func fire(tier: int) -> void:
		harpoon_tier = tier; fire_t = 0.0; set_process(true)
	func sparkle() -> void:
		if reduced: return
		for i in range(8): sparks.append({"a": randf() * TAU, "d": randf_range(.2, .55), "t": -i * .04})
		set_process(true)
	func _process(delta: float) -> void:
		if fire_t >= 0.0:
			fire_t += delta
			if fire_t > (0.6 if reduced else .95): fire_t = -1.0
		for s in sparks: s.t += delta
		sparks = sparks.filter(func(s): return s.t < .7)
		if fire_t < 0.0 and sparks.is_empty(): set_process(false)
		queue_redraw()
	func _draw() -> void:
		ShipArt.draw(self, centre, hull_px, tiers)
		if fire_t >= 0.0:
			var nose := centre + ShipArt.nose_offset(hull_px, tiers)
			var cell := hull_px * .42
			var reach := minf(nose.y + global_position.y - 40.0, cell * 2.2)
			var k: float
			var slack: float
			if reduced: k = 1.0; slack = .15
			elif fire_t < .32: k = 1.0 - pow(1.0 - fire_t / .32, 3.0); slack = .6
			elif fire_t < .5: k = 1.0; slack = .15
			else: var r := (fire_t - .5) / .45; k = 1.0 - r * r; slack = .9
			var tip := nose - Vector2(0, cell * Harpoon.length(harpoon_tier) + reach * k)
			var tail := tip + Vector2(0, cell * Harpoon.length(harpoon_tier))
			if tail.y < nose.y - 1.0: Harpoon.rope(self, nose, tail, cell, slack, fire_t, 1.0, harpoon_tier)
			Harpoon.harpoon(self, tip, -PI / 2, cell, true, harpoon_tier)
		for s in sparks:
			if s.t < 0.0: continue
			var at: Vector2 = centre + Vector2.from_angle(s.a) * hull_px * float(s.d) + Vector2(0, -s.t * 40.0)
			draw_circle(at, hull_px * .025 * (1.0 - s.t / .7), Color(1, .9, .4, 1.0 - s.t / .7))

## Card art: a part sprite, the fired harpoon, or a power-up glyph on a dark tile.
class PartIcon extends Control:
	var id := ""
	var tier := 1
	var texture: Texture2D
	var glyph: Texture2D
	var dim := false
	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		if glyph != null:
			var tile := StyleBoxFlat.new(); tile.bg_color = Color("1c3542"); tile.set_corner_radius_all(int(size.x * .2))
			tile.border_color = Color("0c1d26"); tile.set_border_width_all(maxi(1, int(size.x * .02)))
			draw_style_box(tile, r)
			var color := Color("8aa3ad", .55) if dim else WorkshopBook.tier_color(tier)
			var g := Rect2(r.position + r.size * .14, r.size * .72)
			if not dim:
				for i in range(3):
					var grow := (i + 1) * size.x * .025
					draw_texture_rect(glyph, g.grow(grow), false, Color(color, .16))
			draw_texture_rect(glyph, g, false, color)
		elif id == "harpoon":
			var cell := size.y * .62
			var tip := Vector2(size.x * .5, size.y * .08)
			# Pointing up (tip at the top); harpoon() returns the tail, where the rope coils.
			var tail := Harpoon.harpoon(self, tip, -PI / 2, cell, true, tier)
			var colors: Array = Harpoon.style(tier).rope
			var coil := PackedVector2Array()
			for i in range(13):
				var t := i / 12.0
				coil.append(Vector2(size.x * .5 + sin(t * TAU * 1.2) * size.x * .1, tail.y + t * size.y * .16))
			draw_polyline(coil, colors[0], size.x * .06, true)
			draw_polyline(coil, colors[1], size.x * .035, true)
		elif texture != null:
			var fit := texture.get_size() * minf(size.x * .82 / texture.get_width(), size.y * .84 / texture.get_height())
			draw_texture_rect(texture, Rect2((size - fit) * .5, fit), false)

## Pips (look levels ringed), the power-up trend chevron, and the MAX stamp.
class RowMarks extends Control:
	var levels := 1
	var level := 1
	var looks: Array = []
	var pip_origin := Vector2.ZERO
	var unit := 1.0
	var maxed := false
	var stamp := Rect2()
	var chevron := Vector2(-1, -1)
	var font: Font
	func _draw() -> void:
		for i in range(levels):
			var at := pip_origin + Vector2(i * 30.0, 0) * unit
			var r := Rect2(at, Vector2(22, 11) * unit)
			var on := i < level
			var col := (Color("b2502d") if maxed else Color("c9893c")) if on else Color("e6cfa8")
			var box := StyleBoxFlat.new(); box.bg_color = col; box.set_corner_radius_all(int(6 * unit))
			if (i + 1) in looks.map(func(l): return int(l)):
				box.border_color = Color(TEAL, .55); box.set_border_width_all(maxi(1, int(2.5 * unit))); box.expand_margin_left = 3 * unit; box.expand_margin_right = 3 * unit; box.expand_margin_top = 3 * unit; box.expand_margin_bottom = 3 * unit
			draw_style_box(box, r)
		if chevron.x >= 0.0:
			draw_polyline(PackedVector2Array([chevron + Vector2(0, 9) * unit, chevron + Vector2(8, 1) * unit, chevron + Vector2(16, 9) * unit]), TEAL, 4.0 * unit, true)
		if maxed and stamp.has_area():
			var c := stamp.get_center()
			draw_set_transform(c, deg_to_rad(-8), Vector2.ONE)
			var half := stamp.size * .5
			var ink := Color("c43d2b", .87)
			var box := StyleBoxFlat.new(); box.bg_color = Color.TRANSPARENT; box.border_color = ink; box.set_border_width_all(int(5 * unit)); box.set_corner_radius_all(int(14 * unit))
			draw_style_box(box, Rect2(-half, stamp.size))
			var fs := int(40 * unit)
			var w := font.get_string_size("MAX", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			draw_string(font, Vector2(-w * .5, fs * .36), "MAX", HORIZONTAL_ALIGNMENT_LEFT, -1, fs, ink)
			draw_set_transform(Vector2.ZERO)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	font = Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 850}
	heavy = Typography.body()
	heavy.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 950}
	room = RoomArt.new(); room.texture = ShipArt.texture("room.png"); room.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(room)
	sign_label = _label(self, heavy); sign_label.text = "Workshop"; sign_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; sign_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	sign_label.add_theme_color_override("font_color", Color("5a2f12"))
	door = _flat_button("Back to the Sushi Bar"); add_child(door)
	door.pressed.connect(func(): leave())
	door_tag = Panel.new(); door_tag.mouse_filter = Control.MOUSE_FILTER_IGNORE; door.add_child(door_tag)
	door_label = _label(door_tag, heavy); door_label.text = "‹  Sushi Bar"; door_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; door_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	cradle = TextureRect.new(); cradle.texture = ShipArt.texture("cradle.png"); cradle.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; cradle.stretch_mode = TextureRect.STRETCH_SCALE; cradle.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(cradle)
	ship = ShipCanvas.new(); ship.mouse_filter = Control.MOUSE_FILTER_IGNORE; ship.set_process(false); add_child(ship)
	hero = _flat_button("Test-fire the harpoon"); add_child(hero)
	hero.pressed.connect(func(): ship.fire(_tier("harpoon")))
	salvage_pill = Panel.new(); salvage_pill.mouse_filter = Control.MOUSE_FILTER_IGNORE; add_child(salvage_pill)
	salvage_icon = TextureRect.new(); salvage_icon.texture = load("res://assets/expedition/kit/gold-00.png"); salvage_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; salvage_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; salvage_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE; salvage_pill.add_child(salvage_icon)
	salvage_label = _label(salvage_pill, heavy); salvage_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	tray = Panel.new(); tray.mouse_filter = Control.MOUSE_FILTER_STOP; tray.accessibility_name = "Upgrades"; add_child(tray)
	tray_face = PopupSkin.make_face(tray, wood.texture("wood-grain"))
	for entry in GROUPS:
		var tab := GameButton.new(); tab.toggle_mode = true; tab.tone = GameButton.Tone.MAPLE; tab.radius = 28.0
		tab.text = entry[1]; tab.accessibility_name = entry[1]
		tab.pressed.connect(func(): select_group(entry[0]))
		tray.add_child(tab); tabs.append(tab)
	catalog_backing = Panel.new(); catalog_backing.mouse_filter = Control.MOUSE_FILTER_STOP; catalog_backing.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW; tray.add_child(catalog_backing)
	catalog_shade = PopupSkin.inner_shadow(catalog_backing)
	catalog = ScrollContainer.new(); catalog.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; catalog.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER; catalog.follow_focus = true; catalog_backing.add_child(catalog)
	content = VBoxContainer.new(); content.size_flags_horizontal = Control.SIZE_EXPAND_FILL; content.add_theme_constant_override("separation", 0); catalog.add_child(content)
	hide()

func _label(parent: Node, face: Font) -> Label:
	var value := Label.new()
	value.add_theme_font_override("font", face)
	value.add_theme_color_override("font_color", INK)
	value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(value)
	return value

func _flat_button(accessible: String) -> Button:
	var value := Button.new(); value.accessibility_name = accessible; value.flat = true
	for treatment in ["normal", "hover", "pressed", "disabled", "focus"]: value.add_theme_stylebox_override(treatment, StyleBoxEmpty.new())
	return value

func _tier(id: String) -> int:
	return int(state.get("workshop", {}).get("gear", {}).get("tiers", {}).get(id, 1))

func _track(id: String) -> Dictionary:
	for row in state.get("workshop", {}).get("tracks", []):
		if row.id == id: return row
	return {}

func open(value: Dictionary) -> void:
	focused_before = get_viewport().gui_get_focus_owner()
	state = value; group = "equipment"; _signature = ""
	show(); _build_rows(); refresh(value); layout(area, safe_top)
	ship.fire_t = -1.0; ship.sparks.clear()
	var first := _first_upgrade()
	# Programmatic focus keeps its ring hidden until the player navigates by keys.
	if first != null: first.grab_focus(true)
	else: door.grab_focus(true)

func _first_upgrade() -> Button:
	for id in rows:
		if rows[id].has("buy") and not rows[id].buy.disabled and rows[id].buy.visible: return rows[id].buy
	return null

func select_group(id: String) -> void:
	if group == id: _sync_tabs(); return
	group = id; _signature = ""
	_build_rows(); refresh(state); layout(area, safe_top)
	tabs[0 if id == "equipment" else 1].grab_focus(true)

func leave() -> void:
	if not visible or interaction_blocked: return
	close_requested.emit(door.get_global_rect().get_center() - get_global_rect().position)

func _build_rows() -> void:
	for row in rows.values(): row.row.queue_free()
	rows.clear()
	for entry in WorkshopBook.tracks():
		if entry.group != group: continue
		var id: String = entry.id
		var row := Control.new(); row.mouse_filter = Control.MOUSE_FILTER_PASS; row.size_flags_horizontal = Control.SIZE_EXPAND_FILL; content.add_child(row)
		var art_box := Panel.new(); art_box.mouse_filter = Control.MOUSE_FILTER_IGNORE; row.add_child(art_box)
		var icon := PartIcon.new(); icon.id = id; icon.mouse_filter = Control.MOUSE_FILTER_IGNORE; art_box.add_child(icon)
		if entry.group == "powerup": icon.glyph = load("res://assets/workshop/glyphs/%s.svg" % id)
		var new_tag := Panel.new(); new_tag.mouse_filter = Control.MOUSE_FILTER_IGNORE; row.add_child(new_tag)
		var new_label := _label(new_tag, heavy); new_label.text = "NEW"; new_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; new_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER; new_label.add_theme_color_override("font_color", Color("fff9ec"))
		var name_label := _label(row, heavy); name_label.text = COPY[id].name
		var lv := Panel.new(); lv.mouse_filter = Control.MOUSE_FILTER_IGNORE; row.add_child(lv)
		var lv_label := _label(lv, heavy); lv_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; lv_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER; lv_label.add_theme_color_override("font_color", Color("7a5431"))
		var line_a := _label(row, font); line_a.add_theme_color_override("font_color", MUTED); line_a.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var current := _label(row, heavy)
		var arrow := _label(row, heavy); arrow.text = "→"; arrow.add_theme_color_override("font_color", Color("b39070"))
		var next := _label(row, heavy); next.add_theme_color_override("font_color", TEAL)
		var marks := RowMarks.new(); marks.font = heavy; marks.mouse_filter = Control.MOUSE_FILTER_IGNORE; row.add_child(marks)
		var buy := GameButton.new(); buy.tone = GameButton.Tone.MAPLE; buy.radius = 40.0; buy.caption_px = 32.0
		buy.verb = "Upgrade"; buy.cost_icon = salvage_icon.texture; row.add_child(buy)
		buy.pressed.connect(func(): _request(id))
		var divider := ColorRect.new(); divider.color = Color(.72, .56, .35, .22); divider.mouse_filter = Control.MOUSE_FILTER_IGNORE; row.add_child(divider)
		rows[id] = {"row": row, "art_box": art_box, "icon": icon, "new_tag": new_tag, "new_label": new_label, "name": name_label, "lv": lv, "lv_label": lv_label,
			"line_a": line_a, "current": current, "arrow": arrow, "next": next, "marks": marks, "buy": buy, "divider": divider, "group": entry.group}

func _format(id: String, v: float) -> String:
	match id:
		"hull": return str(int(round(v)))
		"harpoon": return "%.1f×" % v
		"collector": return "%.1f×" % (v / WorkshopBook.value("collector", 1))
	return ""

func refresh(value: Dictionary) -> void:
	if not visible: return
	state = value
	var next_signature := JSON.stringify([value.get("workshop"), group, interaction_blocked])
	if next_signature == _signature: return
	_signature = next_signature
	var view: Dictionary = value.workshop
	salvage_label.text = str(int(view.salvage))
	salvage_pill.accessibility_name = "%d salvage" % int(view.salvage)
	for id in rows:
		var row: Dictionary = rows[id]
		var t := _track(id)
		var lvl := int(t.level)
		var maxed: bool = t.max
		row.lv_label.text = "Lv %d" % lvl
		row.icon.tier = int(t.tier)
		row.icon.dim = id == "launch" and float(t.value) <= 0.0
		if row.group == "equipment" and id != "harpoon": row.icon.texture = ShipArt.texture("parts/%s-%d.png" % [id, int(t.tier)])
		row.icon.queue_redraw()
		row.new_tag.visible = t.new
		if row.group == "equipment":
			row.line_a.text = COPY[id].stat
			row.current.text = _format(id, float(t.value))
			row.arrow.visible = not maxed; row.next.visible = not maxed
			row.next.text = _format(id, float(t.next_value))
			row.current.add_theme_color_override("font_color", Color("7a3c18") if maxed else INK)
		else:
			row.line_a.text = COPY[id].does
			row.current.visible = false; row.arrow.visible = false
			row.next.visible = true
			row.next.text = "Fully upgraded" if maxed else (COPY[id].get("unlock", "") if float(t.value) <= 0.0 else COPY[id].better)
			row.next.add_theme_color_override("font_color", Color("7a3c18") if maxed else TEAL)
		row.marks.levels = int(t.max_level); row.marks.level = lvl; row.marks.looks = t.looks; row.marks.maxed = maxed
		row.buy.visible = not maxed
		row.buy.disabled = interaction_blocked or not t.affordable
		row.buy.cost = str(int(t.cost)) if not maxed else ""
		row.buy.accessibility_name = "Upgrade %s to level %d for %d salvage" % [COPY[id].name, lvl + 1, int(t.cost)] if not maxed else ""
		row.buy.accessibility_description = "" if t.affordable else "Not enough salvage"
		row.row.accessibility_name = "%s, level %d of %d%s" % [COPY[id].name, lvl, int(t.max_level), ", maximum" if maxed else ""]
	_sync_tabs()
	ship.tiers = view.gear.tiers; ship.harpoon_tier = _tier("harpoon"); ship.queue_redraw()
	hero.accessibility_name = "Test-fire the harpoon"
	door.disabled = interaction_blocked
	layout(area, safe_top)

func _sync_tabs() -> void:
	for i in range(GROUPS.size()):
		var id: String = GROUPS[i][0]
		tabs[i].set_pressed_no_signal(id == group)
		var ready := false
		for t in state.get("workshop", {}).get("tracks", []):
			if t.group == id and t.affordable: ready = true
		tabs[i].dot = ready and id != group
		tabs[i].selected = id == group

func _request(id: String) -> void:
	if interaction_blocked or not visible or not rows.has(id) or rows[id].buy.disabled: return
	var t := _track(id)
	# The token names this exact purchase (track and the level it buys from), so
	# a replayed or doubled press never pays twice; a later press buys the next level.
	upgrade_requested.emit({"type": "workshop_upgrade", "id": id, "token": "%s:%d" % [id, int(t.level)]})

## After a committed upgrade: test-fire a new harpoon, sparkle a new look.
func upgraded(result: Dictionary) -> void:
	if not visible: return
	var id := str(result.get("id", ""))
	if id == "harpoon": ship.fire(int(result.get("tier", 1)))
	if result.get("new_look", false) and id in ["hull", "collector"]: ship.reduced = reduced_motion; ship.sparkle()
	if rows.has(id) and not rows[id].buy.disabled and rows[id].buy.visible: rows[id].buy.grab_focus(true)
	elif rows.has(id): catalog.grab_focus(true)

func _text(label: Label, bounds: Rect2, pixels: float) -> void:
	label.add_theme_font_size_override("font_size", maxi(1, int(pixels * unit)))
	label.position = bounds.position * unit
	label.size = bounds.size * unit

func _string_width(face: Font, text: String, pixels: float) -> float:
	return face.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, maxi(1, int(pixels * unit))).x / unit

func layout(value: Rect2, inset := 0.0) -> void:
	area = value; safe_top = inset
	if tray == null or value.size.x <= 0: return
	var physical := maxf(.001, get_viewport_transform().get_scale().x)
	unit = value.size.x / 720.0
	var W := value.size.x
	var H := value.size.y
	var origin := value.position
	# Room: anchored to the top and cover-fitted; capped on wide windows.
	var room_w := H * .62 if W > H * .62 else maxf(W, H * ROOM_SIZE.x / ROOM_SIZE.y)
	var scale := room_w / ROOM_SIZE.x
	room_rect = Rect2(Vector2((W - room_w) * .5, 0), ROOM_SIZE * scale)
	room.position = origin; room.size = value.size; room.rect = room_rect; room.queue_redraw()
	var to_room := func(r: Array) -> Rect2: return Rect2(origin + room_rect.position + Vector2(r[0], r[1]) * scale, Vector2(r[2] - r[0], r[3] - r[1]) * scale)
	var sign_rect: Rect2 = to_room.call([283, 323, 547, 420])
	sign_label.position = sign_rect.position; sign_label.size = sign_rect.size
	# Fitted to the board inside its bolts (about 76% of the plank).
	var sign_px := minf(sign_rect.size.x * .16, sign_rect.size.y * .48)
	sign_label.add_theme_font_size_override("font_size", maxi(1, int(sign_px)))
	var door_rect: Rect2 = to_room.call([45, 290, 210, 530])
	door.position = door_rect.position; door.size = door_rect.size
	door.custom_minimum_size = Vector2.ONE * 44.01 / physical
	var tag_size := Vector2(maxf(150.0 * unit, _string_width(heavy, door_label.text, 30) * unit + 40 * unit), 64 * unit)
	door_tag.position = Vector2((door.size.x - tag_size.x) * .5, door.size.y - tag_size.y * .55); door_tag.size = tag_size
	door_tag.add_theme_stylebox_override("panel", _pill(Color("fff3d8"), tag_size.y * .5))
	door_label.position = Vector2.ZERO; door_label.size = tag_size; door_label.add_theme_font_size_override("font_size", int(28 * unit))
	# Salvage balance, top right in the same cream pill as the restaurant HUD.
	var pill_h := 92.0 * unit
	var pill_w := (110.0 + _string_width(heavy, salvage_label.text, 40)) * unit
	salvage_pill.position = origin + Vector2(W - pill_w - 30 * unit, maxf(inset - origin.y, 0.0) + 60 * unit)
	salvage_pill.size = Vector2(pill_w, pill_h)
	salvage_pill.add_theme_stylebox_override("panel", _pill(Color("fff3d8"), pill_h * .5))
	salvage_icon.position = Vector2(20, 18) * unit; salvage_icon.size = Vector2(62, 56) * unit
	salvage_label.position = Vector2(90, 0) * unit; salvage_label.size = Vector2(pill_w - 90 * unit, pill_h)
	salvage_label.add_theme_font_size_override("font_size", int(40 * unit))
	# Tray: tabs over the beige catalog, rows compact on short screens.
	var short := H < W * 1.75
	var row_h := (204.0 if short else 222.0) if group == "powerup" else (168.0 if short else 206.0)
	var count := rows.size()
	var bottom_pad := 22.0
	var natural := 18.0 + 88.0 + 16.0 + count * row_h + 8.0 + bottom_pad
	var wall := room_rect.position.y + 540.0 * scale
	var tray_h := minf(natural * unit, maxf(300.0 * unit, H - wall - 240.0 * unit))
	tray.position = origin + Vector2(0, H - tray_h)
	tray.size = Vector2(W, tray_h + 40 * unit) # rounded bottom corners sit off screen
	var shadow := PopupSkin.flat(Color.TRANSPARENT, 48 * unit)
	shadow.shadow_color = Color(.35, .18, .05, .22); shadow.shadow_size = int(10 * unit); shadow.shadow_offset = Vector2(0, -2) * unit
	tray.add_theme_stylebox_override("panel", shadow)
	PopupSkin.layout_face(tray_face, tray.size, unit)
	tray_face.material.set_shader_parameter("corner_radius", 48 * unit)
	var ref_w := W / unit
	for i in range(tabs.size()):
		var tab := tabs[i]
		var tab_w := (ref_w - 32 - 12) / 2.0
		tab.position = Vector2(16 + i * (tab_w + 12), 18) * unit; tab.size = Vector2(tab_w, 88) * unit
		tab.caption_px = 30.0; tab.fit(unit, physical)
	catalog_backing.position = Vector2(16, 122) * unit
	catalog_backing.size = Vector2(ref_w - 32, maxf(80, tray_h / unit - 122 - bottom_pad)) * unit
	catalog_backing.add_theme_stylebox_override("panel", PopupSkin.flat(Color("fff1d3"), 36 * unit))
	PopupSkin.layout_inner_shadow(catalog_shade, Rect2(Vector2.ZERO, catalog_backing.size), 36 * unit, unit)
	catalog.position = Vector2(24, 0) * unit; catalog.size = Vector2(catalog_backing.size.x - 48 * unit, catalog_backing.size.y)
	var rw := catalog.size.x / unit
	var index := 0
	for id in rows:
		var row: Dictionary = rows[id]
		row.row.custom_minimum_size = Vector2(0, row_h) * unit; row.row.size = Vector2(catalog.size.x, row_h * unit)
		# Square tile, centred in the row, so icons and glyphs keep their proportions.
		var art := minf(118.0, row_h - 48.0)
		var art_y := (row_h - art) * .5
		row.art_box.position = Vector2(0, art_y) * unit; row.art_box.size = Vector2(art, art) * unit
		row.art_box.add_theme_stylebox_override("panel", PopupSkin.flat(Color.TRANSPARENT if row.group == "powerup" else Color("f7dfb4"), 28 * unit))
		row.icon.position = Vector2.ZERO; row.icon.size = row.art_box.size; row.icon.queue_redraw()
		# Sticker on the tile's top edge, inside the catalog's clip.
		row.new_tag.position = Vector2((art - 70) * .5, art_y - 15) * unit; row.new_tag.size = Vector2(70, 30) * unit
		row.new_tag.add_theme_stylebox_override("panel", PopupSkin.flat(Color("ff6a50"), 15 * unit))
		row.new_label.position = Vector2.ZERO; row.new_label.size = row.new_tag.size; row.new_label.add_theme_font_size_override("font_size", int(18 * unit))
		var text_x := 140.0
		var text_w := rw - text_x - 170.0
		var top := 22.0 if short else 28.0
		_text(row.name, Rect2(text_x, top, text_w, 44), 32)
		var name_w := _string_width(heavy, row.name.text, 32)
		row.lv.position = Vector2(text_x + name_w + 12, top + 8) * unit; row.lv.size = Vector2(_string_width(heavy, row.lv_label.text, 20) + 24, 30) * unit
		row.lv.add_theme_stylebox_override("panel", PopupSkin.flat(Color("f2dcb4"), 15 * unit))
		row.lv_label.position = Vector2.ZERO; row.lv_label.size = row.lv.size; row.lv_label.add_theme_font_size_override("font_size", int(20 * unit))
		var pips_y := row_h - (38.0 if short else 46.0) if row.group == "equipment" else top + 160.0
		if row.group == "equipment":
			_text(row.line_a, Rect2(text_x, top + 46, text_w, 30), 21)
			var value_y := top + 74
			var cur_w := _string_width(heavy, row.current.text, 36)
			_text(row.current, Rect2(text_x, value_y, cur_w + 4, 48), 36)
			_text(row.arrow, Rect2(text_x + cur_w + 10, value_y + 4, 30, 44), 28)
			_text(row.next, Rect2(text_x + cur_w + 46, value_y, text_w - cur_w - 46, 48), 36)
			row.marks.chevron = Vector2(-1, -1)
		else:
			_text(row.line_a, Rect2(text_x, top + 46, text_w, 56), 22)
			var trend_y := top + 116.0
			_text(row.next, Rect2(text_x + 26, trend_y - 6, text_w - 26, 40), 27)
			row.marks.chevron = Vector2(text_x, trend_y + 6) * unit if row.next.text != "Fully upgraded" else Vector2(-1, -1)
			if row.next.text == "Fully upgraded": _text(row.next, Rect2(text_x, trend_y - 6, text_w, 40), 23)
		row.marks.position = Vector2.ZERO; row.marks.size = row.row.size; row.marks.unit = unit
		row.marks.pip_origin = Vector2(text_x, pips_y) * unit
		row.marks.stamp = Rect2(Vector2(rw - 156, (row_h - 82) * .5) * unit, Vector2(138, 82) * unit)
		row.marks.queue_redraw()
		row.buy.position = Vector2(rw - 156, (row_h - 112) * .5) * unit; row.buy.size = Vector2(156, 112) * unit
		row.buy.fit(unit, physical)
		row.divider.position = Vector2(0, 0); row.divider.size = Vector2(rw * unit, maxf(1.0, 2 * unit)); row.divider.visible = index > 0
		index += 1
	# Cradle and ship in the free floor between the wall and the tray.
	var free_top := origin.y + wall + 12 * unit
	var free_bottom := tray.position.y - 12 * unit
	var free_h := free_bottom - free_top
	var cradle_h := maxf(80 * unit, minf(free_h * .9, room_w * .5 / CRADLE_ASPECT))
	var cradle_w := cradle_h * CRADLE_ASPECT
	var cradle_pos := Vector2(origin.x + (W - cradle_w) * .5, free_top + (free_h - cradle_h) * .5)
	cradle.position = cradle_pos; cradle.size = Vector2(cradle_w, cradle_h)
	hero.position = cradle_pos; hero.size = cradle.size
	ship.position = Vector2(origin.x, origin.y); ship.size = value.size
	ship.hull_px = cradle_h * .7
	ship.centre = cradle_pos - origin + Vector2(cradle_w * .5, cradle_h * .52)
	ship.queue_redraw()

func _pill(color: Color, radius: float) -> StyleBoxFlat:
	var style := PopupSkin.flat(color, radius)
	style.border_color = Color("e1bc85"); style.set_border_width_all(maxi(1, int(2 * unit)))
	style.shadow_color = Color(.45, .27, .1, .35); style.shadow_size = maxi(1, int(2 * unit)); style.shadow_offset = Vector2(0, 5) * unit
	return style

func cancel_interactions() -> void:
	for id in rows: rows[id].buy.release()
	for tab in tabs: tab.release()

func _input(event: InputEvent) -> void:
	if not visible or interaction_blocked: return
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE: leave(); get_viewport().set_input_as_handled()
		elif event.keycode in [KEY_LEFT, KEY_RIGHT] and get_viewport().gui_get_focus_owner() in tabs:
			select_group("powerup" if group == "equipment" else "equipment"); get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_WINDOW_FOCUS_OUT] and is_node_ready(): cancel_interactions()
