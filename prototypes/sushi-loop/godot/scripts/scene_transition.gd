extends Control
## The game's one scene transition (#28), used for every scene switch: an iris
## closes onto what the player tapped (navy, with a cream rim like the harpoon
## strike's focus circle), a short loading beat plays while the next scene is
## built (the salvage chunk bobbing over rising bubbles, at least MIN_LOAD),
## then the iris reopens on the new scene's point of interest. Input is blocked
## throughout; reduced motion fades through navy instead. Approved prototype:
## design/workshop-preview/transition.js.
const NAVY := Color("0f2433")
const RIM := Color("fff1d3")
const CLOSE_SECONDS := .42
const OPEN_SECONDS := .46
const MIN_LOAD := .45
var reduced_motion := false
var _icon: Texture2D
var _centre := Vector2.ZERO
var _radius := 0.0
var _closed := false
var _fade := 0.0
var _loading := false
var _clock := 0.0
var busy := false
var _mask: ColorRect

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 100
	_icon = load("res://assets/expedition/kit/gold-00.png")
	_mask = ColorRect.new(); _mask.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mask.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); _mask.show_behind_parent = true
	var material := ShaderMaterial.new(); material.shader = load("res://scripts/iris.gdshader"); _mask.material = material
	add_child(_mask)
	hide()

func _cover(point: Vector2) -> float:
	return Vector2(maxf(point.x, size.x - point.x), maxf(point.y, size.y - point.y)).length() + 8.0

## Close on `from`, run `swap` (the next scene is built behind the navy), then
## reopen on `to.call()` (or the centre). Returns when the new scene is shown.
## A second call while one runs does nothing (repeated taps).
func play(from: Vector2, swap: Callable, to := Callable()) -> void:
	if busy: return
	busy = true
	show(); mouse_filter = Control.MOUSE_FILTER_STOP
	_loading = false; _clock = 0.0
	if reduced_motion:
		_closed = true; _fade = 0.0
		await _animate(func(k): _fade = k, .15)
		swap.call()
		await get_tree().process_frame
		await _animate(func(k): _fade = 1.0 - k, .15)
	else:
		_closed = false; _fade = 0.0; _centre = from; _radius = _cover(from); _sync_mask()
		await _animate(func(k): _radius = lerpf(_cover(from), 0.0, _ease(k)), CLOSE_SECONDS)
		_closed = true; _loading = true; _sync_mask()
		var started := Time.get_ticks_msec()
		swap.call()
		# Let the new scene lay out before reading its focus point.
		await get_tree().process_frame
		var wait := MIN_LOAD - (Time.get_ticks_msec() - started) / 1000.0
		if wait > 0.0: await get_tree().create_timer(wait).timeout
		_loading = false; _closed = false
		_centre = to.call() if to.is_valid() else size * .5
		_radius = 0.0; _sync_mask()
		await _animate(func(k): _radius = lerpf(0.0, _cover(_centre), _ease(k)), OPEN_SECONDS)
	hide(); mouse_filter = Control.MOUSE_FILTER_IGNORE
	busy = false

func _ease(k: float) -> float:
	return 4.0 * k * k * k if k < .5 else 1.0 - pow(-2.0 * k + 2.0, 3.0) / 2.0

func _animate(step: Callable, seconds: float) -> void:
	var tween := create_tween()
	tween.tween_method(func(k: float): step.call(k); _sync_mask(); queue_redraw(), 0.0, 1.0, seconds)
	await tween.finished

func _sync_mask() -> void:
	var unit := minf(size.x, size.y * 9.0 / 16.0) / 390.0
	var material: ShaderMaterial = _mask.material
	_mask.visible = not reduced_motion
	material.set_shader_parameter("centre", _centre)
	material.set_shader_parameter("radius", 0.0 if _closed else _radius)
	material.set_shader_parameter("rim_width", 5.0 * unit)

func _process(delta: float) -> void:
	if not visible: return
	_clock += delta
	if _loading: queue_redraw()

func _draw() -> void:
	var unit := minf(size.x, size.y * 9.0 / 16.0) / 390.0
	if reduced_motion:
		draw_rect(Rect2(Vector2.ZERO, size), Color(NAVY, _fade))
		return
	# The navy and its rim are the shader mask (iris.gdshader); the loader draws on top.
	if _loading:
		var c := size * .5
		var bob := sin(_clock * 4.5) * 5.0 * unit
		var tilt := sin(_clock * 4.5) * .1
		for i in range(3):
			var k := fposmod(_clock / 1.1 + i / 3.0, 1.0)
			var at := c + Vector2((i - 1) * 18.0 * unit, 34.0 * unit - k * 70.0 * unit)
			draw_arc(at, (4.0 if i != 1 else 3.0) * unit, 0, TAU, 16, Color(.75, .91, 1, .8 * sin(PI * k)), 2.0 * unit, true)
		var icon_size := Vector2(52, 41) * unit
		draw_set_transform(c + Vector2(0, bob), tilt, Vector2.ONE)
		draw_texture_rect(_icon, Rect2(-icon_size * .5, icon_size), false)
		draw_set_transform(Vector2.ZERO)
