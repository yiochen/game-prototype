extends Control
## Collected cash flying to the money counter (#61). The wallet is credited in
## the saved state before a flight starts; flights only delay what the counter
## shows, and `landed` reports each share as it arrives.

signal landed(amount: int)

const SECONDS := 0.55
const STAGGER := 0.07

var icon: Texture2D
var target := Vector2.ZERO
var _flights: Array = []
var _clock := 0.0

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

## Splits `amount` across `notes` flying from `from` (this control's space).
func launch(from: Vector2, amount: int, notes: int, spread: float) -> void:
	notes = maxi(1, notes)
	for index in notes:
		var share := roundi(float(amount) * (index + 1) / notes) - roundi(float(amount) * index / notes)
		var jitter := Vector2(randf_range(-0.5, 0.5), randf_range(-0.4, 0.4)) * spread
		_flights.append({"from": from + jitter, "start": _clock + index * STAGGER, "amount": share, "spin": randf_range(160.0, 260.0)})

func pending() -> int:
	var total := 0
	for flight in _flights: total += int(flight.amount)
	return total

## Lands everything at once, for reduced motion or leaving the scene.
func finish() -> void:
	var total := pending()
	_flights.clear()
	if total > 0: landed.emit(total)
	queue_redraw()

func _process(delta: float) -> void:
	_clock += delta
	if _flights.is_empty(): return
	var arrived := 0
	var remaining: Array = []
	for flight in _flights:
		if _clock - float(flight.start) >= SECONDS: arrived += int(flight.amount)
		else: remaining.append(flight)
	_flights = remaining
	if arrived > 0: landed.emit(arrived)
	queue_redraw()

func _draw() -> void:
	if icon == null: return
	# Notes fly at about the HUD icon's size, scaled with the screen unit.
	var fit := 48.0 * float(get_meta("unit", 1.0)) / maxf(1.0, float(icon.get_width()))
	for flight in _flights:
		var t := (_clock - float(flight.start)) / SECONDS
		if t < 0.0: continue
		t = clampf(t, 0.0, 1.0)
		var eased := t * t * (3.0 - 2.0 * t)
		var start: Vector2 = flight.from
		var control := (start + target) * 0.5 + Vector2(size.x * 0.12, -size.y * 0.04)
		var u := 1.0 - eased
		var at := start * u * u + control * 2.0 * u * eased + target * eased * eased
		var zoom := (1.1 - 0.45 * eased) * fit
		draw_set_transform(at, deg_to_rad(float(flight.spin) * eased), Vector2.ONE * zoom)
		draw_texture(icon, -Vector2(icon.get_size()) * 0.5, Color(1, 1, 1, 1.0 if t < 0.92 else (1.0 - t) / 0.08))
	draw_set_transform(Vector2.ZERO)
