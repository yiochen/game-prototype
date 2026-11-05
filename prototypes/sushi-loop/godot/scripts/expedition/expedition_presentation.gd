extends Control
## Expedition screen (issue #21): underwater preparation, travel HUD, Pause,
## early-return confirmation, resume countdown and the results receipt.
## Preparation is on-screen text while the ship cruises the route's launch
## lead-in (easing into a hover at its end), with a Sushi Bar exit; pressing
## anywhere else starts the dive (and steers when it lands on an arrow).
## Gameplay and --expedition-gallery share this presentation. Commands go
## through `commander` (session.command); this node never edits state itself.
##
## Issue #22: shield pickups, shield bumps and portal rides arrive as advance
## events; a portal transition holds travel until the view's whirlpool iris
## finishes. During the passage ride the arrows dim and a quiet label says the
## current is steering.
##
## Issue #23: in the encounter a wide resistance pill appears under the HUD
## row and the contextual Harpoon button sits between the steering arrows.
## A shot about to strike slows the whole game (presentation time only; the
## rules just receive smaller elapsed steps) while the view's focus circle
## closes on the impact; "Hooked!" and "It got away" are plain outlined text
## on the water. The hooked handoff holds travel and dims the arrows.
##
## Surfaces reuse the approved shared family (maple popup face, cream capsules,
## vermilion primary, round cream control). Outcome backgrounds are tinted
## scrims until the ImageGen results family is produced and approved.
const ExpeditionView = preload("res://scripts/expedition/expedition_view.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const HarpoonButton = preload("res://scripts/expedition/harpoon_button.gd")

signal returned_to_restaurant
signal save_requested
signal departed

const INK := Color("633b21")
const TITLES := {"complete": "Expedition complete", "returned_early": "Returned early", "hull_depleted": "Hull depleted"}
const SCRIMS := {"complete": Color(.07, .32, .42, .55), "returned_early": Color(.10, .22, .36, .6), "hull_depleted": Color(.22, .12, .20, .6)}

var commander: Callable
var state_provider: Callable
var safe_top := 0.0
var mode := "hidden"          # hidden | prep | travel | results
var overlay := "none"         # none | paused | confirm | countdown
var countdown := 0.0
var snapshot: Dictionary = {}
var result: Dictionary = {}
var area := Rect2()
var reduced_motion := false
var gallery := false
var focused_before: Control

var view: ExpeditionView
var skin := UISkin.new()
var wood := Wood.new()
var hull_pill: Panel
var hull_track: Panel
var hull_fill: Panel
var hull_icon: TextureRect
var salvage_pill: Panel
var salvage_icon: TextureRect
var salvage_label: Label
var pause_button: Button
var scrim: ColorRect
var cards: Dictionary = {}
var countdown_number: Label
var countdown_caption: Label
var receipt: Dictionary = {}
var damage_flash: TextureRect
var prep_title: Label
var prep_text: Label
var prep_hint: Label
var exit_button: Button
var ride_note: Label
var toast: Label
var _toast_left := 0.0
var _hull_pulse := 0.0
var _hit_flash := 0.0
var _salvage_pop := 0.0
var harpoon_button: HarpoonButton
var resistance_pill: Panel
var resistance_icon: TextureRect
var resistance_track: Panel
var resistance_fill: Panel
var callout_title: Label
var callout_text: Label
var _callout_left := 0.0
var _callout_age := 0.0
## Game speed for the strike's slow motion (1 = normal).
var time_scale := 1.0
var _slow_hold := 0.0
var _prep_seed := 0
var _prep_lead: Dictionary = {}
var _prep_y := 0.0
var _keys := {}

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	view = ExpeditionView.new(); add_child(view)
	view.steered.connect(func(input: float): if mode == "travel" and overlay == "none": _command({"type": "expedition_steer", "input": input}))
	view.pressed_down.connect(func(): if mode == "prep": start(true))
	# Impact: red vignette at the screen edges, above the playfield and below the HUD.
	damage_flash = TextureRect.new(); damage_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	damage_flash.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; damage_flash.stretch_mode = TextureRect.STRETCH_SCALE
	damage_flash.texture = _vignette(); damage_flash.modulate.a = 0.0; add_child(damage_flash)
	hull_pill = _pill("Hull"); hull_track = Panel.new(); hull_track.mouse_filter = Control.MOUSE_FILTER_IGNORE; hull_pill.add_child(hull_track)
	hull_fill = Panel.new(); hull_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE; hull_track.add_child(hull_fill)
	hull_icon = TextureRect.new(); hull_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE; hull_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	hull_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; hull_icon.texture = _ship_icon(); hull_pill.add_child(hull_icon)
	salvage_pill = _pill("Salvage this expedition")
	salvage_icon = TextureRect.new(); salvage_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE; salvage_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	salvage_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; salvage_icon.texture = load("res://assets/expedition/kit/gold-00.png"); salvage_pill.add_child(salvage_icon)
	salvage_label = _label(salvage_pill, 900); salvage_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	pause_button = Button.new(); pause_button.icon = _pause_icon(); pause_button.expand_icon = true; pause_button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_button.accessibility_name = "Pause"; add_child(pause_button)
	pause_button.add_theme_font_override("font", _font(900))
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: pause_button.add_theme_color_override(key, INK)
	pause_button.pressed.connect(pause)
	scrim = ColorRect.new(); scrim.mouse_filter = Control.MOUSE_FILTER_STOP; scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(scrim)
	# Pause: title and side-by-side Resume / Return early only.
	_card("paused", "Paused", "", [["Return early", false, func(): _show_overlay("confirm")], ["Resume", true, resume]])
	_card("confirm", "Return early?", "Keep your haul. No completion bonus.", [["Stay paused", false, func(): _show_overlay("paused")], ["Return", true, return_early]])
	prep_title = _label(self, 950); prep_title.text = "Submarine ready"
	prep_text = _label(self, 750); prep_text.text = "Hold the left or right arrow to steer. Let go to run straight."
	prep_hint = _label(self, 900); prep_hint.text = "Touch anywhere to dive"
	for label in [prep_title, prep_text, prep_hint]:
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		label.add_theme_color_override("font_color", Color("fff6df"))
		label.add_theme_color_override("font_shadow_color", Color(.02, .1, .2, .7)); label.add_theme_constant_override("shadow_offset_y", 3)
	exit_button = Button.new(); exit_button.text = "Sushi Bar"; exit_button.accessibility_name = "Back to the Sushi Bar"
	exit_button.add_theme_font_override("font", _font(850)); exit_button.set_meta("primary", false); exit_button.focus_mode = Control.FOCUS_ALL
	exit_button.pressed.connect(close_prep); add_child(exit_button)
	ride_note = _label(self, 850); ride_note.text = "The current carries you"; ride_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast = _label(self, 850); toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	for label in [ride_note, toast]:
		label.add_theme_color_override("font_color", Color("eafcff"))
		var pill := PopupSkin.flat(Color(.016, .094, .227, .5), 999)
		pill.content_margin_left = 14; pill.content_margin_right = 14
		label.add_theme_stylebox_override("normal", pill)
	_card("results", "", "", [["Restaurant", true, finish_results]])
	for row in ["pickups", "bonus", "total"]:
		var name_label := _label(cards.results.panel, 800); var value_label := _label(cards.results.panel, 900); value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		receipt[row] = [name_label, value_label]
	receipt.note = [_label(cards.results.panel, 700)]
	resistance_pill = _pill("Creature resistance")
	resistance_icon = TextureRect.new(); resistance_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE; resistance_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	resistance_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; resistance_icon.texture = load("res://assets/expedition/creature/eel-icon.svg"); resistance_pill.add_child(resistance_icon)
	resistance_track = Panel.new(); resistance_track.mouse_filter = Control.MOUSE_FILTER_IGNORE; resistance_pill.add_child(resistance_track)
	resistance_fill = Panel.new(); resistance_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE; resistance_track.add_child(resistance_fill)
	harpoon_button = HarpoonButton.new(); add_child(harpoon_button)
	harpoon_button.fired.connect(fire)
	# Callouts sit straight on the water: cream type with a navy outline.
	callout_title = _label(self, 950); callout_text = _label(self, 900)
	for label in [callout_title, callout_text]:
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.add_theme_color_override("font_color", Color("fff6df"))
		label.add_theme_color_override("font_outline_color", Color("0b2f63"))
		label.add_theme_color_override("font_shadow_color", Color(.02, .1, .2, .45))
		label.add_theme_constant_override("shadow_offset_y", 5); label.add_theme_constant_override("shadow_offset_x", 0)
	# Encounter pieces stay under the Pause scrim and cards, like the rest of the HUD.
	for node in [resistance_pill, harpoon_button, callout_title, callout_text]: move_child(node, scrim.get_index())
	countdown_number = _label(self, 950); countdown_number.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; countdown_number.add_theme_color_override("font_color", Color("fff6df"))
	countdown_caption = _label(self, 850); countdown_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; countdown_caption.text = "Returning to ship..."
	countdown_caption.add_theme_color_override("font_color", Color("fff6df"))
	for label in [countdown_number, countdown_caption]:
		label.add_theme_color_override("font_shadow_color", Color(.02, .1, .2, .6)); label.add_theme_constant_override("shadow_offset_y", 3)
	hide()

func _font(weight: int) -> Font:
	var font := Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): weight}
	return font

func _label(parent: Node, weight: int) -> Label:
	var label := Label.new(); label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_override("font", _font(weight)); label.add_theme_color_override("font_color", INK)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER; parent.add_child(label)
	return label

## Clear centre fading to warning red at the edges and corners.
static func _vignette() -> Texture2D:
	var gradient := Gradient.new()
	gradient.offsets = PackedFloat32Array([0.0, .58, .82, 1.0])
	gradient.colors = PackedColorArray([Color(.9, .08, .05, 0), Color(.9, .08, .05, 0), Color(.92, .1, .06, .38), Color(.95, .12, .08, .8)])
	var texture := GradientTexture2D.new()
	texture.gradient = gradient; texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(.5, .5); texture.fill_to = Vector2(1.0, .5); texture.width = 128; texture.height = 128
	return texture

## Two rounded ink bars, matching the HUD's ink colour.
static func _pause_icon() -> Texture2D:
	var image := Image.create(48, 48, false, Image.FORMAT_RGBA8)
	for y in range(48):
		for x in range(48):
			var inside := y >= 12 and y < 36 and ((x >= 14 and x < 21) or (x >= 27 and x < 34))
			image.set_pixel(x, y, INK if inside else Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(image)

func _pill(accessible: String) -> Panel:
	var panel := Panel.new(); panel.mouse_filter = Control.MOUSE_FILTER_IGNORE; panel.accessibility_name = accessible; add_child(panel)
	return panel

## The travel clip's first frame, cropped to the hull, as the meter icon.
func _ship_icon() -> Texture2D:
	var data: Dictionary = view.pieces.objects["submarine-yellow"]
	var rect: Array = data.clips[0].directions.S.rects[0]
	var atlas := AtlasTexture.new()
	atlas.atlas = load("res://assets/expedition/" + str(data.clips[0].directions.S.image))
	atlas.region = Rect2(float(rect[0]) + float(rect[2]) * .25, float(rect[1]) + float(rect[3]) * .44, float(rect[2]) * .5, float(rect[3]) * .4)
	return atlas

func _card(id: String, heading: String, body: String, actions: Array) -> void:
	var panel := Panel.new(); panel.mouse_filter = Control.MOUSE_FILTER_STOP; panel.accessibility_name = heading; add_child(panel)
	var face := PopupSkin.make_face(panel, wood.texture("wood-grain"))
	var title := _label(panel, 950); title.text = heading; title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; title.add_theme_color_override("font_color", Color("592c10"))
	var text := _label(panel, 750); text.text = body; text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var buttons: Array = []
	for action in actions:
		var button := Button.new(); button.text = action[0]; button.accessibility_name = action[0]
		button.add_theme_font_override("font", _font(850)); button.set_meta("primary", action[1]); panel.add_child(button)
		button.pressed.connect(action[2]); buttons.append(button)
	cards[id] = {"panel": panel, "face": face, "title": title, "text": text, "buttons": buttons}
	panel.hide()

func _command(request: Dictionary) -> Dictionary:
	if not commander.is_valid(): return {"ok": false}
	return commander.call(request)

func _now() -> float: return Time.get_unix_time_from_system()

# ------------------------------------------------------------ flow

## Ready dock tap: preview the next route behind the preparation card. No charge is spent.
func open_prep(value: Dictionary) -> void:
	snapshot = value; mode = "prep"; overlay = "none"; result = {}
	focused_before = get_viewport().gui_get_focus_owner()
	_prep_seed = int(value.expedition.next_seed)
	_prep_lead = Book.launch(_prep_seed)
	_prep_y = float(_prep_lead.bottom)
	_sync_prep(0.0)
	view.snap_camera()
	view.accessibility_name = "Underwater preparation. Touch anywhere to dive, then hold the left or right arrow to steer."
	show(); _refresh_visibility(); layout(area)
	# No focused control: Enter/Space starts, Back returns to the Sushi Bar.
	if get_viewport().gui_get_focus_owner() != null: get_viewport().gui_get_focus_owner().release_focus()

func close_prep() -> void:
	mode = "hidden"; hide(); returned_to_restaurant.emit()

## `by_touch`: the starting press stays held (and steers if it is on an arrow).
func start(by_touch := false) -> void:
	if mode != "prep": return
	var outcome := _command({"type": "expedition_start", "now": _now(), "y": _prep_y})
	if not outcome.get("ok", false): close_prep(); return
	mode = "travel"; overlay = "none"
	if not by_touch: view.release_controls()
	view.steering_enabled = true; view.resume_controls()
	view.accessibility_name = "Expedition. Hold the left or right arrow to steer."
	departed.emit(); save_requested.emit(); _refresh_visibility()

## Reopen after close/background: unfinished travel waits behind Paused.
func resume_suspended(value: Dictionary) -> void:
	snapshot = value
	if value.expedition.run != null:
		mode = "travel"; _command({"type": "expedition_pause"}); _show_overlay("paused")
		view.accessibility_name = "Expedition. Hold the left or right arrow to steer."
		_sync_view(0.0); view.snap_camera(); show()
	elif value.expedition.result != null:
		show_results(value.expedition.result)

func pause() -> void:
	if mode != "travel" or overlay != "none": return
	_command({"type": "expedition_pause"}); view.release_controls(); _keys.clear(); view.key_input = 0.0
	harpoon_button.release()
	_show_overlay("paused"); save_requested.emit()

## Harpoon: one shot per fresh press while the shooting window is open.
func fire() -> void:
	if mode != "travel" or overlay != "none": return
	_command({"type": "expedition_fire"})

func _callout(title: String, text: String) -> void:
	callout_title.text = title; callout_text.text = text
	_callout_left = 2.6; _callout_age = 0.0; layout(area)

## App backgrounded or closed: freeze behind Paused (not an early return).
func suspend() -> void:
	if mode == "travel" and overlay in ["none", "countdown"]:
		_command({"type": "expedition_pause"}); _show_overlay("paused")
	view.release_controls(); harpoon_button.release()

func resume() -> void:
	# The countdown keeps movement and timers frozen; the engine resumes after it.
	countdown = 0.0 if reduced_motion else 3.0
	_show_overlay("countdown")
	if countdown <= 0.0: _finish_countdown()

func _finish_countdown() -> void:
	_command({"type": "expedition_resume"}); view.resume_controls(); _show_overlay("none")

func return_early() -> void:
	var outcome := _command({"type": "expedition_return_early", "now": _now()})
	if outcome.get("ok", false): show_results(outcome.result); save_requested.emit()

func show_results(value: Dictionary) -> void:
	result = value; mode = "results"; overlay = "none"; show()
	var outcome := str(value.outcome)
	cards.results.title.text = TITLES[outcome]; cards.results.panel.accessibility_name = TITLES[outcome]
	receipt.pickups[0].text = "Pickups"; receipt.pickups[1].text = str(int(value.pickups))
	receipt.bonus[0].text = "Completion bonus"; receipt.bonus[1].text = ("+%d" % int(value.bonus)) if int(value.bonus) > 0 else "0"
	receipt.total[0].text = "Total salvage"; receipt.total[1].text = str(int(value.total))
	receipt.note[0].text = "" if outcome == "complete" else ("Finish the route to earn the completion bonus." if outcome == "returned_early" else "The hull gave out before the finish.")
	scrim.color = SCRIMS[outcome]
	_refresh_visibility(); layout(area)
	cards.results.buttons[0].grab_focus()

func finish_results() -> void:
	_command({"type": "expedition_acknowledge", "id": result.get("id")})
	result = {}; mode = "hidden"; hide(); save_requested.emit(); returned_to_restaurant.emit()

func _show_overlay(value: String) -> void:
	overlay = value; _refresh_visibility(); layout(area)
	if value == "paused": cards.paused.buttons[1].grab_focus()
	elif value == "confirm": cards.confirm.buttons[0].grab_focus()

## Android Back: Pause while travelling; step back through cards otherwise.
func back() -> bool:
	if not visible: return false
	match mode:
		"prep": close_prep()
		"results": finish_results()
		"travel":
			if overlay == "none": pause()
			elif overlay == "confirm": _show_overlay("paused")
	return true

func _unhandled_key_input(event: InputEvent) -> void:
	if not visible: return
	if mode == "prep" and event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled(); start()
	elif mode == "travel" and overlay == "none" and event is InputEventKey and event.keycode == KEY_SPACE:
		# Space fires on a fresh press; key repeat never fires again.
		if event.pressed and not event.echo: fire()
		get_viewport().set_input_as_handled()
	# Keyboard fallback for the stick: held arrow keys steer, release runs straight.
	elif mode == "travel" and overlay == "none" and event is InputEventKey and event.keycode in [KEY_LEFT, KEY_RIGHT] and not event.echo:
		_keys[event.keycode] = event.pressed
		view.key_input = (1.0 if _keys.get(KEY_RIGHT, false) else 0.0) - (1.0 if _keys.get(KEY_LEFT, false) else 0.0)
		_command({"type": "expedition_steer", "input": view.key_input})
		get_viewport().set_input_as_handled()

# ------------------------------------------------------------ frame

func update(value: Dictionary, delta: float) -> void:
	snapshot = value
	if not visible: return
	var run = value.expedition.run
	if mode == "travel" and run == null and value.expedition.result != null:
		show_results(value.expedition.result); return
	if mode == "travel" and run != null:
		if overlay == "countdown" and not gallery:
			countdown -= delta
			if countdown <= 0.0: _finish_countdown()
		if overlay == "none": _update_slow_motion(delta)
		var game_delta := delta * time_scale
		# A portal transition holds travel until the iris opens on the far side.
		if overlay == "none" and not gallery and not view.transitioning():
			var outcome := _command({"type": "expedition_advance", "elapsed": game_delta, "now": _now()})
			for event in outcome.get("events", []):
				match event.type:
					"pickup": view.burst(Vector2(float(event.x), float(event.y))); _salvage_pop = 1.0
					"impact":
						_hull_pulse = 1.0; _hit_flash = 1.0; view.hit()
					"shield":
						view.shield_burst(Vector2(float(event.x), float(event.y))); _show_toast("Shield! No collision damage")
					"shield_bump": view.shield_bump(Vector2(float(event.x), float(event.y)))
					"hooked":
						view.hooked(); _slow_hold = float(Book.definition().encounter.slow_motion_hold_seconds)
						_callout("Hooked!", "The chase begins next"); save_requested.emit()
					"creature_escaped": _callout("It got away", "No recipe this time"); save_requested.emit()
					"passage_enter", "passage_exit":
						view.begin_transition("enter" if event.type == "passage_enter" else "exit", Vector2(float(event.from_x), float(event.from_y)))
						save_requested.emit()
					"ended":
						show_results(event.result); save_requested.emit(); return
			if state_provider.is_valid(): snapshot.expedition = state_provider.call()
		_sync_view(game_delta)
	elif mode == "prep":
		# Cruise up the launch lead-in, easing to a hover before the canyon proper.
		if not reduced_motion:
			var near := clampf((_prep_y - float(_prep_lead.hover)) / 3.0, 0.0, 1.0)
			_prep_y = maxf(float(_prep_lead.hover), _prep_y - float(Book.definition().forward_rows_per_second) * near * near * (3.0 - 2.0 * near) * delta)
		_sync_prep(delta)
		prep_hint.modulate.a = 1.0 if reduced_motion else .55 + .45 * (.5 + .5 * sin(view.time * 3.2))
	_refresh_hud(delta)

## Strike slow motion: ease down while a shot is about to hit, hold briefly
## after the hook, then ease back. Real time drives it, so it never stalls.
func _update_slow_motion(delta: float) -> void:
	var run = snapshot.expedition.run
	var rules: Dictionary = Book.definition().encounter
	var slow := float(rules.slow_motion_scale)
	var target := 1.0
	var point = Book.strike_point(run, float(rules.slow_motion_lookahead_rows)) if run != null else null
	if _slow_hold > 0.0:
		_slow_hold -= delta; target = slow
	elif point != null:
		target = slow
		view.focus_at = view._origin() + point * view._cell()
	time_scale += (target - time_scale) * minf(1.0, delta * (14.0 if target < time_scale else 3.5))
	if absf(time_scale - 1.0) < .01: time_scale = 1.0
	var encounter = run.get("encounter") if run != null else null
	if encounter is Dictionary and encounter.state == "hooked" and view._creature_shown: view.focus_at = view.hook_point()
	view.focus_amount = clampf((1.0 - time_scale) / (1.0 - slow), 0.0, 1.0)

func _sync_prep(delta: float) -> void:
	view.steering_enabled = false; view.controls_visible = true; view.reduced_motion = reduced_motion
	view.sync({"seed": _prep_seed, "x": _prep_lead.x, "y": _prep_y, "protection": 0.0, "collected": []}, delta, not gallery)

func _sync_view(delta: float) -> void:
	var run = snapshot.expedition.run
	if run == null: return
	view.steering_enabled = overlay == "none"; view.controls_visible = overlay == "none"
	# The passage current steers, and a hooked creature holds the ship: the arrows dim.
	var encounter = run.get("encounter")
	var hooked: bool = encounter is Dictionary and encounter.state == "hooked"
	view.controls_disabled = run.get("passage") != null or view.transitioning() or hooked
	var aiming: bool = encounter is Dictionary and encounter.state == "aiming"
	harpoon_button.visible = mode == "travel" and aiming
	if aiming:
		var cooldown := float(Book.definition().encounter.cooldown_seconds)
		var ready: bool = encounter.harpoon == null and float(encounter.cooldown) <= 0.0
		harpoon_button.state = "paused" if overlay != "none" else ("ready" if ready else "reloading")
		harpoon_button.progress = 1.0 if ready else clampf(1.0 - float(encounter.cooldown) / cooldown, 0.0, 1.0)
	elif harpoon_button.held: harpoon_button.release()
	resistance_pill.visible = mode == "travel" and encounter is Dictionary and encounter.state != "escaped"
	ride_note.visible = mode == "travel" and overlay == "none" and run.get("passage") != null and not view.transitioning()
	view.reduced_motion = reduced_motion
	view.sync(run, delta, overlay == "none" and not gallery)

func _show_toast(text: String) -> void:
	toast.text = text; _toast_left = 1.6; layout(area)

func _refresh_hud(delta: float) -> void:
	_callout_left = maxf(0.0, _callout_left - delta); _callout_age += delta
	for label in [callout_title, callout_text]:
		label.visible = _callout_left > 0.0 and mode == "travel"
		label.modulate.a = minf(1.0, _callout_left * 2.5)
	# Pop in: a quick overshoot, skipped for reduced motion.
	var pop := 1.0 if reduced_motion else 1.0 + .25 * sin(minf(1.0, _callout_age / .35) * PI) * (1.0 - minf(1.0, _callout_age / .35))
	callout_title.pivot_offset = callout_title.size / 2; callout_title.scale = Vector2.ONE * pop
	_toast_left = maxf(0.0, _toast_left - delta)
	toast.visible = _toast_left > 0.0 and mode == "travel"
	toast.modulate.a = minf(1.0, _toast_left * 2.0)
	var run = snapshot.get("expedition", {}).get("run")
	if run == null: return
	# The hull icon glows while the shield or the passage protects it.
	hull_icon.modulate = Color(.8, 1.15, 1.3) if float(run.get("shield", 0.0)) > 0.0 or run.get("passage") != null else Color.WHITE
	salvage_label.text = str(int(run.salvage)); salvage_pill.accessibility_description = "%d salvage this expedition" % int(run.salvage)
	var fraction := float(run.get("hull_fraction", 1.0))
	var low: bool = run.get("low_hull", false)
	hull_pill.accessibility_description = "Hull %d%%%s%s" % [int(round(fraction * 100)), ", low" if low else "", ", shield" if float(run.get("shield", 0.0)) > 0.0 else ""]
	_hull_pulse = maxf(0.0, _hull_pulse - delta * 2.5)
	_hit_flash = maxf(0.0, _hit_flash - delta * 2.2)
	damage_flash.modulate.a = _hit_flash * (.6 if reduced_motion else 1.0)
	# Salvage pill pops when a pickup lands.
	_salvage_pop = maxf(0.0, _salvage_pop - delta * 4.0)
	salvage_pill.pivot_offset = salvage_pill.size / 2
	salvage_pill.scale = Vector2.ONE * (1.0 + (0.0 if reduced_motion else .14 * sin(_salvage_pop * PI)))
	# Low hull: warning colour and a gentle pulse inside the meter only.
	var pulse := 0.0 if reduced_motion else (.5 + .5 * sin(view.time * 5.0) if low else 0.0)
	var color := Color("e2563d").lerp(Color("ff8a5c"), pulse) if low else Color("49b85a")
	var unit := area.size.x / 390.0
	hull_fill.size = Vector2(maxf(0.0, (hull_track.size.x - 6 * unit) * fraction), hull_track.size.y - 6 * unit)
	hull_fill.position = Vector2(3, 3) * unit
	hull_fill.add_theme_stylebox_override("panel", PopupSkin.flat(color.lerp(Color.WHITE, _hull_pulse * .5), 8 * unit))

func _refresh_visibility() -> void:
	var travelling := mode == "travel"
	hull_pill.visible = travelling; salvage_pill.visible = travelling; pause_button.visible = travelling
	pause_button.disabled = overlay != "none"
	view.visible = mode in ["prep", "travel", "results"]
	scrim.visible = mode == "results" or overlay in ["paused", "confirm"] or mode == "prep"
	# Preparation's light scrim lets the press reach the playfield.
	scrim.mouse_filter = Control.MOUSE_FILTER_IGNORE if mode == "prep" else Control.MOUSE_FILTER_STOP
	if mode == "prep": scrim.color = Color(.03, .12, .22, .3)
	elif mode == "travel": scrim.color = Color(.03, .12, .22, .45)
	damage_flash.visible = travelling
	cards.paused.panel.visible = travelling and overlay == "paused"
	cards.confirm.panel.visible = travelling and overlay == "confirm"
	for node in [prep_title, prep_text, prep_hint, exit_button]: node.visible = mode == "prep"
	if not travelling:
		ride_note.visible = false; toast.visible = false; harpoon_button.visible = false; resistance_pill.visible = false
		callout_title.visible = false; callout_text.visible = false
	cards.results.panel.visible = mode == "results"
	countdown_number.visible = travelling and overlay == "countdown"
	countdown_caption.visible = countdown_number.visible

func _process(_delta: float) -> void:
	if overlay == "countdown" and countdown_number.visible:
		countdown_number.text = str(maxi(1, int(ceil(countdown))))

# ------------------------------------------------------------ layout

func layout(value: Rect2) -> void:
	area = value
	if area.size.x <= 0 or view == null: return
	var unit := area.size.x / 390.0
	var physical := maxf(.001, get_viewport_transform().get_scale().x)
	view.position = area.position; view.size = area.size
	damage_flash.position = area.position; damage_flash.size = area.size
	var top := area.position.y + maxf(safe_top - area.position.y, 0.0) + 14 * unit
	# Stable top row: hull left, run salvage beside it, Pause right.
	hull_pill.position = Vector2(area.position.x + 12 * unit, top); hull_pill.size = Vector2(150, 50) * unit
	skin.apply_panel(hull_pill, "coin-panel", unit * 390.0 / 720.0)
	hull_icon.position = Vector2(8, 6) * unit; hull_icon.size = Vector2(38, 38) * unit
	hull_track.position = Vector2(50, 17) * unit; hull_track.size = Vector2(88, 16) * unit
	hull_track.add_theme_stylebox_override("panel", PopupSkin.flat(Color("6b4a2c"), 8 * unit))
	salvage_pill.size = Vector2(108, 50) * unit; salvage_pill.position = Vector2(hull_pill.position.x + hull_pill.size.x + 10 * unit, top)
	skin.apply_panel(salvage_pill, "coin-panel", unit * 390.0 / 720.0)
	salvage_icon.position = Vector2(10, 4) * unit; salvage_icon.size = Vector2(42, 42) * unit
	salvage_label.position = Vector2(54, 0) * unit; salvage_label.size = Vector2(46, 50) * unit
	salvage_label.add_theme_font_size_override("font_size", maxi(1, int(22 * unit)))
	PopupSkin.close_button(pause_button, unit * 390.0 / 720.0 * 1.04, physical)
	pause_button.position = Vector2(area.end.x - 12 * unit - pause_button.size.x, top)
	pause_button.add_theme_constant_override("icon_max_width", int(30 * unit))
	for label in [ride_note, toast]:
		label.add_theme_font_size_override("font_size", maxi(1, int(15 * unit)))
		label.size = Vector2(0, 0); label.reset_size()
	var edge := minf(area.size.x / 7.0 * 1.6, area.size.y * .18)
	ride_note.position = Vector2(area.get_center().x - ride_note.size.x / 2, area.end.y - edge * .22 * 1.6 - edge / 2 - ride_note.size.y / 2)
	toast.position = Vector2(area.get_center().x - toast.size.x / 2, area.position.y + area.size.y * .2)
	# Encounter: a wide resistance pill under the HUD row; Harpoon between the arrows.
	resistance_pill.size = Vector2(250, 50) * unit
	resistance_pill.position = Vector2(area.get_center().x - resistance_pill.size.x / 2, top + 60 * unit)
	skin.apply_panel(resistance_pill, "coin-panel", unit * 390.0 / 720.0)
	resistance_icon.position = Vector2(10, 9) * unit; resistance_icon.size = Vector2(36, 32) * unit
	resistance_track.position = Vector2(52, 17) * unit; resistance_track.size = Vector2(178, 16) * unit
	resistance_track.add_theme_stylebox_override("panel", PopupSkin.flat(Color("6b4a2c"), 8 * unit))
	resistance_fill.position = Vector2(3, 3) * unit; resistance_fill.size = resistance_track.size - Vector2(6, 6) * unit
	resistance_fill.add_theme_stylebox_override("panel", PopupSkin.flat(Color("4f8fe6"), 5 * unit))
	var button_size := maxf(76 * unit, 48.0 / physical)
	harpoon_button.size = Vector2.ONE * button_size
	harpoon_button.position = Vector2(area.get_center().x - button_size / 2, area.end.y - edge * .22 * 1.6 - edge / 2 - button_size / 2)
	callout_title.add_theme_font_size_override("font_size", maxi(1, int(46 * unit)))
	callout_title.add_theme_constant_override("outline_size", maxi(1, int(10 * unit)))
	callout_text.add_theme_font_size_override("font_size", maxi(1, int(18 * unit)))
	callout_text.add_theme_constant_override("outline_size", maxi(1, int(7 * unit)))
	callout_title.position = Vector2(area.position.x, area.position.y + area.size.y * .52 - 40 * unit); callout_title.size = Vector2(area.size.x, 56 * unit)
	callout_text.position = Vector2(area.position.x, callout_title.position.y + 54 * unit); callout_text.size = Vector2(area.size.x, 26 * unit)
	_layout_card(cards.paused, unit, physical, 150)
	_layout_card(cards.confirm, unit, physical, 186)
	_layout_prep(unit, physical, top)
	_layout_card(cards.results, unit, physical, 330)
	_layout_receipt(unit)
	countdown_number.position = Vector2(area.position.x, area.get_center().y - 90 * unit); countdown_number.size = Vector2(area.size.x, 110 * unit)
	countdown_number.add_theme_font_size_override("font_size", maxi(1, int(84 * unit)))
	countdown_caption.position = Vector2(area.position.x, area.get_center().y + 20 * unit); countdown_caption.size = Vector2(area.size.x, 40 * unit)
	countdown_caption.add_theme_font_size_override("font_size", maxi(1, int(20 * unit)))
	_refresh_hud(0.0)

## Preparation: Sushi Bar exit in the HUD row, title and hint over the open water.
func _layout_prep(unit: float, physical: float, top: float) -> void:
	exit_button.position = Vector2(area.position.x + 12 * unit, top)
	exit_button.size = Vector2(132 * unit, maxf(48.0 / physical, 48.0 * unit))
	exit_button.custom_minimum_size = Vector2.ONE * 44.01 / physical
	_style_button(exit_button, unit)
	exit_button.add_theme_font_size_override("font_size", maxi(1, int(17 * unit)))
	var y := area.position.y + area.size.y * .3
	prep_title.position = Vector2(area.position.x + 20 * unit, y); prep_title.size = Vector2(area.size.x - 40 * unit, 48 * unit)
	prep_title.add_theme_font_size_override("font_size", maxi(1, int(36 * unit)))
	prep_text.position = Vector2(area.position.x + 36 * unit, y + 52 * unit); prep_text.size = Vector2(area.size.x - 72 * unit, 48 * unit)
	prep_text.add_theme_font_size_override("font_size", maxi(1, int(17 * unit)))
	prep_hint.position = Vector2(area.position.x + 20 * unit, y + 132 * unit); prep_hint.size = Vector2(area.size.x - 40 * unit, 36 * unit)
	prep_hint.add_theme_font_size_override("font_size", maxi(1, int(22 * unit)))

func _style_button(button: Button, unit: float) -> void:
	var primary: bool = button.get_meta("primary")
	for treatment in ["normal", "hover", "pressed", "disabled"]:
		var style := PopupSkin.flat(Color("ff624b") if primary else Color("fff1d5"), 26 * unit)
		if treatment == "pressed": style.bg_color = style.bg_color.darkened(.06)
		if treatment == "disabled" and primary: style.bg_color = Color("dfc6a1")
		style.shadow_color = Color("bd4528") if primary else Color("b98450"); style.shadow_size = maxi(1, int(unit)); style.shadow_offset = Vector2(0, 1 if treatment == "pressed" else 3) * unit
		button.add_theme_stylebox_override(treatment, style)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: button.add_theme_color_override(key, Color("fff9ed") if primary else INK)
	var focus := PopupSkin.flat(Color.TRANSPARENT, 26 * unit); focus.set_border_width_all(maxi(1, int(2 * unit))); focus.border_color = Color("32636b")
	button.add_theme_stylebox_override("focus", focus)

func _layout_card(card: Dictionary, unit: float, physical: float, height: float, bottom := false) -> void:
	var panel: Panel = card.panel
	var action_height := maxf(48.0 / physical, 48.0 * unit)
	panel.size = Vector2(area.size.x - 40 * unit, maxf(height * unit, action_height + 110 * unit))
	panel.position = Vector2(area.position.x + 20 * unit, area.end.y - panel.size.y - 28 * unit if bottom else area.get_center().y - panel.size.y / 2)
	var shadow := PopupSkin.flat(Color.TRANSPARENT, 25 * unit); shadow.shadow_color = Color(.35, .18, .05, .24); shadow.shadow_size = int(7 * unit); shadow.shadow_offset = Vector2(0, 5) * unit
	panel.add_theme_stylebox_override("panel", shadow)
	PopupSkin.layout_face(card.face, panel.size, unit * 390.0 / 720.0); card.face.material.set_shader_parameter("corner_radius", 25 * unit)
	card.title.position = Vector2(14, 18) * unit; card.title.size = Vector2(panel.size.x - 28 * unit, 34 * unit)
	card.title.add_theme_font_size_override("font_size", maxi(1, int(25 * unit)))
	card.text.position = Vector2(20, 58) * unit; card.text.size = Vector2(panel.size.x - 40 * unit, maxf(0, panel.size.y - action_height - 92 * unit))
	card.text.add_theme_font_size_override("font_size", maxi(1, int(16 * unit)))
	card.text.visible = card.text.text != ""
	var buttons: Array = card.buttons
	var gap := 12 * unit
	var width := (panel.size.x - 28 * unit - gap * (buttons.size() - 1)) / buttons.size()
	for i in range(buttons.size()):
		var button: Button = buttons[i]
		button.position = Vector2(14 * unit + i * (width + gap), panel.size.y - action_height - 18 * unit)
		button.size = Vector2(width, action_height)
		button.custom_minimum_size = Vector2.ONE * 44.01 / physical
		button.add_theme_font_size_override("font_size", maxi(1, int(17 * unit)))
		_style_button(button, unit)

func _layout_receipt(unit: float) -> void:
	var panel: Panel = cards.results.panel
	var y := 70.0 * unit
	for row in ["pickups", "bonus", "total"]:
		var big: bool = row == "total"
		if big: y += 10 * unit
		var labels: Array = receipt[row]
		labels[0].position = Vector2(30 * unit, y); labels[0].size = Vector2(panel.size.x * .6, (44 if big else 34) * unit)
		labels[1].position = Vector2(panel.size.x * .5, y); labels[1].size = Vector2(panel.size.x * .5 - 30 * unit, (44 if big else 34) * unit)
		for label in labels: label.add_theme_font_size_override("font_size", maxi(1, int((26 if big else 18) * unit)))
		y += (44 if big else 34) * unit
	receipt.note[0].position = Vector2(24 * unit, y + 4 * unit); receipt.note[0].size = Vector2(panel.size.x - 48 * unit, 40 * unit)
	receipt.note[0].autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; receipt.note[0].horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	receipt.note[0].add_theme_font_size_override("font_size", maxi(1, int(14 * unit)))
