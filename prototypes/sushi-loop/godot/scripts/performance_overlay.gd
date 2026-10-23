extends Control
## Temporary release-build diagnostics. Wall-clock cadence includes rendering,
## presentation waits and stalls; CPU process time is not GPU time.
const WINDOW_US := 1000000
var samples: Array[PackedInt64Array] = []
var previous_us := 0
var refresh_elapsed := 0.0
var caption := "FPS …  |  frame … ms  |  worst … ms"
var version := str(ProjectSettings.get_setting("application/config/version", ""))
var detail := "Waiting for frame samples"
var font: Font
var font_size := 12
var suspended := false

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	z_index = 100
	font = preload("res://scripts/typography.gd").body()

func reset_samples() -> void:
	samples.clear()
	previous_us = 0
	refresh_elapsed = 0.0

func record_frame(now_us: int, cpu_us := 0) -> void:
	if previous_us > 0 and now_us > previous_us:
		samples.append(PackedInt64Array([now_us, now_us - previous_us, cpu_us]))
	previous_us = now_us
	while not samples.is_empty() and (samples[0][0] <= now_us - WINDOW_US or samples.size() > 512):
		samples.pop_front()

func statistics() -> Dictionary:
	var total := 0.0
	var worst := 0
	var cpu_total := 0.0
	for sample in samples:
		total += sample[1]
		cpu_total += sample[2]
		worst = maxi(worst, sample[1])
	if total <= 0.0:
		return {"fps": 0.0, "average_ms": 0.0, "worst_ms": 0.0, "cpu_ms": 0.0}
	return {"fps": samples.size() * 1000000.0 / total, "average_ms": total / samples.size() / 1000.0, "worst_ms": worst / 1000.0, "cpu_ms": cpu_total / samples.size() / 1000.0}

func _process(delta: float) -> void:
	if suspended: return
	record_frame(Time.get_ticks_usec(), int(Performance.get_monitor(Performance.TIME_PROCESS) * 1000000.0))
	refresh_elapsed += delta
	if refresh_elapsed < 0.25: return
	refresh_elapsed = 0.0
	var stats := statistics()
	caption = "%.0f FPS · %.1f ms · max %.1f ms" % [stats.fps, stats.average_ms, stats.worst_ms]
	detail = "CPU %.1f ms · draws %d · %s" % [stats.cpu_ms, int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)), version]
	queue_redraw()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		suspended = true
		reset_samples()
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		suspended = false
		reset_samples()

func place(area: Rect2, safe_top: float, sky_height: float) -> void:
	var scale_factor := area.size.x / 390.0
	font_size = maxi(int(ceil(10.0 / maxf(0.01, get_viewport_transform().get_scale().y))), int(12 * scale_factor))
	position = Vector2(area.position.x + 6 * scale_factor, safe_top + 2 * scale_factor)
	size = Vector2(area.size.x - 12 * scale_factor, sky_height - safe_top - 4 * scale_factor)
	queue_redraw()

func _draw() -> void:
	if font == null: return
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.015, 0.035, 0.07, 0.84))
	var inset := 5.0 * font_size / 12.0
	var baseline := inset + font.get_ascent(font_size)
	draw_string(font, Vector2(inset, baseline), caption, HORIZONTAL_ALIGNMENT_LEFT, size.x - inset * 2, font_size, Color("e3ffbb"))
	draw_string(font, Vector2(inset, baseline + font.get_height(font_size)), detail, HORIZONTAL_ALIGNMENT_LEFT, size.x - inset * 2, font_size, Color("ffffff"))
