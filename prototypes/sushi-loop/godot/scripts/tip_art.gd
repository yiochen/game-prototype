extends RefCounted
## #61 world presentation for tips, drawn by RestaurantView into its own pass:
## floating cash piles, the tip jar's fill and balance label, tea requests,
## reactions and the short tip effects. Effects are presentation only; every
## amount is already in the saved state when its effect starts.
## Approved composition: design/cash-preview/.

const BOB_SECONDS := 1.7
const BOB_CELLS := 0.07
const TOSS_SECONDS := 0.7
const JAR_FLIGHT_SECONDS := 0.7
const POPUP_SECONDS := 0.9
const LOST_SECONDS := 1.2
const TEA_ACK_SECONDS := 2.2
const HINT_SECONDS := 1.4
const JAR_STATES := [["static", 0.0], ["quarter", 0.375], ["half", 0.64], ["most", 1.0]]
const LABEL := Color("fff3dc")
const LABEL_INK := Color("633b21")
const FULL := Color("e0523a")
const GAIN_INK := Color("174a2f")
const PILES := ["cash-1", "cash-2", "cash-3"]

## Tip jar clip for its fill: the empty jar is the static (unlit) frame.
static func jar_clip(jar: Dictionary) -> String:
	var balance := int(jar.get("balance", 0))
	var capacity := maxi(1, int(jar.get("capacity", 1)))
	if balance <= 0: return "static"
	if balance >= capacity: return "full"
	var fraction := float(balance) / float(capacity)
	for entry in JAR_STATES:
		if fraction < float(entry[1]): return str(entry[0])
	return "most"

static func effect_age(view, effect: Dictionary) -> float:
	return float(view.time) - float(effect.start) - float(effect.get("delay", 0.0))

## Piles still in the air from a toss are drawn by the toss, not on the floor.
static func tossing(view, pile: Dictionary) -> bool:
	for effect in view.tip_effects:
		if effect.kind == "toss" and int(effect.to.x) == int(pile.x) and int(effect.to.y) == int(pile.y) and effect_age(view, effect) < TOSS_SECONDS: return true
	return false

## A floating pile and its floor shadow, registered on its tile centre.
static func draw_pile(view, pile: Dictionary) -> void:
	if tossing(view, pile): return
	var base: Vector2 = view.cell_base(float(pile.x), float(pile.y))
	var phase := 0.0 if view.reduced_motion else (sin(TAU * (float(view.time) / BOB_SECONDS + float(hash(Vector2i(int(pile.x), int(pile.y))) % 97) / 97.0)) + 1.0) * 0.5
	_shadow(view, base, view.cell, 1.0 - 0.22 * phase)
	view.sprite(PILES[clampi(int(pile.get("tier", 0)), 0, 2)], base - Vector2(0, BOB_CELLS * view.cell * phase), "static", "S", 0.0, view.cell)

static func _shadow(view, base: Vector2, pitch: float, scale: float) -> void:
	var center := base + Vector2(0, pitch * 0.16)
	var radius := Vector2(pitch * 0.34, pitch * 0.1) * scale
	view.draw_set_transform(center, 0.0, Vector2(1.0, radius.y / radius.x))
	view.draw_circle(Vector2.ZERO, radius.x, Color(0.23, 0.14, 0.06, 0.28 * scale))
	view.draw_set_transform(Vector2.ZERO)

## Effects and labels above the whole scene, after guests' bubbles.
static func draw_overlay(view) -> void:
	var tips: Dictionary = view.state.get("tips", {})
	var jar: Dictionary = tips.get("jar", {})
	if jar.get("placed", false): _jar_label(view, jar)
	for effect in view.tip_effects:
		var age := effect_age(view, effect)
		if age < 0.0: continue
		match effect.kind:
			"toss": _toss(view, effect, age)
			"jar_flight": _jar_flight(view, effect, age)
			"gain": _gain(view, effect, age)
			"lost": _lost(view, effect, age)
			"hint": _hint(view, jar, age)

static func expire(view) -> void:
	view.tip_effects = view.tip_effects.filter(func(effect): return effect_age(view, effect) < _duration(effect))

static func _duration(effect: Dictionary) -> float:
	match effect.kind:
		"toss": return TOSS_SECONDS
		"jar_flight": return JAR_FLIGHT_SECONDS
		"gain": return POPUP_SECONDS
		"lost": return LOST_SECONDS
		"hint": return HINT_SECONDS
		"tea_ack": return TEA_ACK_SECONDS
		"jar_bounce": return 0.32
	return 1.0

## A guest's tea thanks, shown with the shared happy bubble.
static func tea_ack(view, customer: Dictionary) -> float:
	for effect in view.tip_effects:
		if effect.kind == "tea_ack" and effect.customer_id == customer.get("id"):
			var age := effect_age(view, effect)
			if age >= 0.0 and age < TEA_ACK_SECONDS: return age
	return -1.0

static func jar_squash(view) -> Vector2:
	if view.reduced_motion: return Vector2.ONE
	for effect in view.tip_effects:
		if effect.kind != "jar_bounce": continue
		var t := effect_age(view, effect) / 0.32
		if t >= 0.0 and t < 1.0: return Vector2(1.0 + 0.06 * sin(PI * t), 1.0 - 0.06 * sin(PI * t))
	return Vector2.ONE

static func _arc(view, from: Vector2, to: Vector2, t: float, height_cells: float) -> Vector2:
	var a: Vector2 = view.cell_base(from.x, from.y)
	var b: Vector2 = view.cell_base(to.x, to.y)
	return a.lerp(b, t) - Vector2(0, 4.0 * height_cells * view.cell * t * (1.0 - t))

static func _toss(view, effect: Dictionary, age: float) -> void:
	var to := Vector2(float(effect.to.x), float(effect.to.y))
	var from := Vector2(float(effect.from.x), float(effect.from.y) - 0.45)
	var t := clampf(age / (TOSS_SECONDS * 0.72), 0.0, 1.0)
	var base := _arc(view, from, to, t, 0.7)
	if t >= 1.0:
		# Landing bounce, then the floor pile takes over.
		var s := (age - TOSS_SECONDS * 0.72) / (TOSS_SECONDS * 0.28)
		base -= Vector2(0, view.cell * 0.08 * sin(PI * clampf(s, 0.0, 1.0)))
		_shadow(view, view.cell_base(to.x, to.y), view.cell, 1.0)
	view.sprite(PILES[clampi(int(effect.tier), 0, 2)], base, "static", "S", 0.0, view.cell)

static func _jar_flight(view, effect: Dictionary, age: float) -> void:
	var t := clampf(age / JAR_FLIGHT_SECONDS, 0.0, 1.0)
	var from := Vector2(float(effect.from.x), float(effect.from.y) - 0.6)
	var to := Vector2(float(effect.to.x), float(effect.to.y) - 1.05)
	view.sprite(PILES[clampi(int(effect.tier), 0, 2)], _arc(view, from, to, t, 1.1), "static", "S", 0.0, view.cell * (1.0 - 0.35 * t))

static func _gain(view, effect: Dictionary, age: float) -> void:
	var t := age / POPUP_SECONDS
	var at: Vector2 = view.cell_base(float(effect.x), float(effect.y)) - Vector2(0, view.cell * (float(effect.get("lift", 0.55)) + 0.5 * t))
	outlined_text(view, "+$%d" % int(effect.amount), at, view.cell * 0.3, Color(1, 1, 1, 1.0 - maxf(0.0, t - 0.6) / 0.4), Color(GAIN_INK, 1.0 - maxf(0.0, t - 0.6) / 0.4))

static func _lost(view, effect: Dictionary, age: float) -> void:
	# The tip had nowhere to go: a muted icon fades above the guest.
	var t := age / LOST_SECONDS
	var at: Vector2 = view.cell_base(float(effect.x), float(effect.y)) - Vector2(0, view.cell * (1.35 + 0.25 * t))
	view.sprite("tip-check", at, "static", "S", 0.0, view.cell * 0.8, Color(0.55, 0.55, 0.52, 0.75 * (1.0 - t)))

## The jar is off screen: a small arrow at the scene edge points to where the
## tip went, so it does not read as wallet income.
static func _hint(view, jar: Dictionary, age: float) -> void:
	if not jar.get("placed", false): return
	var target: Vector2 = view.cell_base(float(jar.x), float(jar.y)) - Vector2(0, view.cell * 0.6)
	var area: Rect2 = view.hud_area().grow(-view.cell * 0.35)
	if area.has_point(target): return
	var center := area.get_center()
	var direction := (target - center).normalized()
	var reach := INF
	if absf(direction.x) > 0.001: reach = minf(reach, (area.size.x * 0.5) / absf(direction.x))
	if absf(direction.y) > 0.001: reach = minf(reach, (area.size.y * 0.5) / absf(direction.y))
	var at := center + direction * reach
	var alpha := 1.0 - maxf(0.0, age / HINT_SECONDS - 0.6) / 0.4
	var size: float = view.cell * 0.22
	view.draw_circle(at, size * 1.25, Color(LABEL, 0.92 * alpha))
	var tip := at + direction * size * 0.9
	var side := direction.orthogonal() * size * 0.55
	view.draw_colored_polygon(PackedVector2Array([tip, at - direction * size * 0.3 + side, at - direction * size * 0.3 - side]), Color(LABEL_INK, alpha))

static func _jar_label(view, jar: Dictionary) -> void:
	var full: bool = int(jar.balance) >= int(jar.capacity)
	var text := "FULL · $%d" % int(jar.capacity) if full else "$%d / $%d" % [int(jar.balance), int(jar.capacity)]
	var pixels := int(view.cell * 0.17)
	var width: float = view.font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels).x
	var pulse := 1.0 if not full or view.reduced_motion else 1.0 + 0.1 * maxf(0.0, sin(TAU * float(view.time) / 1.1))
	var center: Vector2 = view.cell_base(float(jar.x), float(jar.y)) - Vector2(0, view.cell * 1.38)
	var box := Rect2(center - Vector2(width * 0.5 + pixels * 0.6, pixels * 0.72) * pulse, Vector2(width + pixels * 1.2, pixels * 1.44) * pulse)
	var style := StyleBoxFlat.new()
	style.bg_color = FULL if full else LABEL
	style.set_corner_radius_all(int(box.size.y * 0.5))
	style.shadow_color = Color(0, 0, 0, 0.2)
	style.shadow_offset = Vector2(0, pixels * 0.12)
	view.draw_style_box(style, box)
	view.draw_string(view.heading, center + Vector2(-width * 0.5 * pulse, pixels * 0.36 * pulse), text, HORIZONTAL_ALIGNMENT_LEFT, -1, int(pixels * pulse), Color.WHITE if full else LABEL_INK)

static func outlined_text(view, text: String, at: Vector2, pixels: float, fill: Color, ink: Color) -> void:
	var size := int(pixels)
	var width: float = view.heading.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var origin := at - Vector2(width * 0.5, -size * 0.35)
	# Stamped outline: font outlines are not available in every render pass.
	var stroke := maxf(2.0, size * 0.09)
	for step in 12:
		var angle := TAU * step / 12.0
		view.draw_string(view.heading, origin + Vector2(cos(angle), sin(angle)) * stroke, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, ink)
	view.draw_string(view.heading, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, fill)
