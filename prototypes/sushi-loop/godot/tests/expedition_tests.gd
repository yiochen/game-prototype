extends SceneTree

const Dive = preload("res://scripts/expedition.gd")
var checks := 0
var failures := 0
var result: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(message)

func fresh(route: int = 0, tutorial: bool = false) -> Control:
	var dive = Dive.new()
	dive.setup(route, {}, tutorial)
	dive.set_process(false)
	return dive

func run() -> void:
	# Save all active encounter timers through a JSON round trip, then remain paused.
	var first = fresh(2)
	first.phase = "pursuit"
	first.ship_x = 415.0
	first.hull = 47.0
	first.resistance = 62.0
	first.attack_warning = 0.83
	first.aim_left = 2.1
	first.grace = 1.1
	first.pickups = 18
	first.objects = [{"kind":"rock", "x":180.0, "y": 500.0, "radius":48.0}]
	var saved: Dictionary = JSON.parse_string(JSON.stringify(first.snapshot()))
	var restored = Dive.new()
	restored.setup(2, {}, false, saved)
	check(restored.paused and restored.hull == 47.0, "Restore must preserve hull and pause")
	check(restored.attack_warning == 0.83 and restored.grace == 1.1, "Restore must preserve attack and grace timers")
	check(restored.resistance == 62.0 and restored.objects.size() == 1, "Restore must preserve capture and obstacles")
	var before: Dictionary = restored.snapshot()
	restored._tick(2.0)
	check(restored.snapshot() == before, "Pause must freeze every simulation timer")
	restored._resume()
	restored._tick(1.0)
	check(restored.attack_warning == 0.83, "Resume countdown must hold encounter timers")
	restored.pointer_x = 300.0
	restored._drag_to(470.0)
	check(restored.ship_x == 415.0 and restored.pointer_x == 470.0, "Countdown drag should anchor without moving")
	restored.resume_countdown = 0.0
	restored._drag_to(480.0)
	check(restored.ship_x == 425.0, "Steering resumes relative to last held pointer")
	first.free()
	restored.free()

	# A press fires once; cooldown cannot be bypassed by another finger or holding.
	var aiming = fresh()
	aiming.phase = "aim"
	aiming._fire()
	aiming._fire()
	check(aiming.shots.size() == 1 and aiming.shot_cooldown > 0, "Fresh press must respect harpoon cooldown")
	aiming.shots = [{"x":360.0,"y":450.0}]
	aiming.creature_x = 360.0
	aiming._tick_shots(0.08)
	check(aiming.phase == "pursuit" and aiming.resistance == 100.0, "Harpoon hooks without removing resistance")
	aiming.ship_x = 360.0
	aiming.creature_clock = 0.0
	aiming._tick_creature(0.1)
	check(aiming.resistance < 100.0, "Following should drain resistance")
	var progress: float = aiming.resistance
	aiming.ship_x = 90.0
	aiming._tick_creature(0.1)
	check(aiming.resistance == progress and aiming.grace > 0.0, "Leaving strip should pause progress and start grace")
	aiming.grace = 2.69
	aiming._tick_creature(0.1)
	check(aiming.phase == "exit" and not aiming.caught, "Expired cable has one pursuit attempt")
	aiming.free()

	# The harpoon finger must not steal or reanchor an existing steering finger.
	var touch = fresh()
	root.add_child(touch)
	touch.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	touch.size = Vector2(720, 1280)
	touch.phase = "aim"
	var finger := InputEventScreenTouch.new()
	finger.index = 0
	finger.pressed = true
	finger.position = Vector2(200, 800)
	touch._input(finger)
	check(touch.pointer == 0 and touch.ship_x == 360.0, "Touch-down anchors without snapping ship")
	var second_finger := InputEventScreenTouch.new()
	second_finger.index = 1
	second_finger.pressed = true
	second_finger.position = Vector2(601, 1114)
	touch._input(second_finger)
	check(touch.pointer == 0 and touch.shots.size() == 1, "Harpoon tap preserves the active steering finger")
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(240, 800)
	touch._input(drag)
	check(touch.ship_x == 400.0, "Steering remains relative after second-finger shooting")
	finger.pressed = false
	touch._input(finger)
	check(touch.pointer == -1, "Finger release stops direct steering")
	touch.free()

	# Modern tall phones add playable water while preserving icon/font aspect.
	# Inject touches through the actual canvas transform at both logical and
	# physical phone resolutions, including the relocated bottom harpoon.
	for dimensions in [Vector2(720, 1280), Vector2(720, 1600), Vector2(1080, 2400)]:
		var responsive = fresh()
		root.add_child(responsive)
		responsive.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
		responsive.size = dimensions
		responsive.phase = "aim"
		var factor: Vector2 = responsive._drawing_scale()
		var canvas_height: float = dimensions.y * 720.0 / dimensions.x
		check(is_equal_approx(factor.x, factor.y), "Artwork and text must use uniform scaling at %s" % dimensions)
		check(is_equal_approx(responsive._canvas_height(), canvas_height), "Canvas must fill actual phone height at %s" % dimensions)
		check(is_equal_approx(responsive._world_y(Dive.SHIP_Y) / canvas_height, Dive.SHIP_Y / Dive.H), "Ship keeps its vertical playfield position at %s" % dimensions)
		for endpoint in [0.0, 1.0]:
			responsive.travel = responsive.travel_duration * endpoint
			responsive.ship_x = 90.0 if endpoint == 0.0 else 630.0
			var ocean: Rect2 = responsive._ocean_rect()
			check(ocean.position.x <= 0.0 and ocean.position.y <= 0.0 and ocean.end.x >= 720.0 and ocean.end.y >= canvas_height, "Painted ocean must cover every viewport edge throughout parallax")
		responsive.ship_x = 360.0
		var steering := InputEventScreenTouch.new()
		steering.index = 0
		steering.pressed = true
		steering.position = responsive.get_global_transform_with_canvas() * (Vector2(200, responsive._world_y(800)) * factor)
		responsive._input(steering)
		var shot_touch := InputEventScreenTouch.new()
		shot_touch.index = 1
		shot_touch.pressed = true
		shot_touch.position = responsive.get_global_transform_with_canvas() * (responsive._harpoon_position() * factor)
		responsive._input(shot_touch)
		check(responsive.pointer == 0 and responsive.shots.size() == 1, "Bottom-anchored harpoon must fire without stealing steering at %s" % dimensions)
		var steering_drag := InputEventScreenDrag.new()
		steering_drag.index = 0
		steering_drag.position = responsive.get_global_transform_with_canvas() * (Vector2(250, responsive._world_y(800)) * factor)
		responsive._input(steering_drag)
		check(is_equal_approx(responsive.ship_x, 410.0), "Horizontal relative steering must remain consistent at %s" % dimensions)
		var pause_touch := InputEventScreenTouch.new()
		pause_touch.index = 2
		pause_touch.pressed = true
		pause_touch.position = responsive.get_global_transform_with_canvas() * (Vector2(640, 80) * factor)
		responsive._input(pause_touch)
		check(responsive.paused, "Pause must stay near physical top at %s" % dimensions)
		if canvas_height > Dive.H:
			responsive._press(Vector2(350, 733))
			check(responsive.paused, "Old unshifted Resume location must not resume a tall-phone card")
		var resume_touch := InputEventScreenTouch.new()
		resume_touch.index = 3
		resume_touch.pressed = true
		resume_touch.position = responsive.get_global_transform_with_canvas() * (Vector2(350, 733 + responsive._middle_offset()) * factor)
		responsive._input(resume_touch)
		check(not responsive.paused and responsive.resume_countdown > 0.0 and responsive.pointer == -1, "Centered Resume must consume its touch and start countdown at %s" % dimensions)
		responsive.resume_countdown = 0.0
		responsive.lesson = "shoot"
		responsive._press(Vector2(350, 784 + responsive._middle_offset()))
		check(responsive.lesson.is_empty(), "Centered teaching card must retain its matching hit region")
		responsive._update_headlight()
		check(is_equal_approx(responsive.headlight.position.y / factor.y, responsive._world_y(Dive.SHIP_Y) - 424.0), "Headlight stays attached to proportionate submarine")
		responsive.free()

	var lesson = fresh(0, true)
	check(lesson.lesson == "steer", "Protected first dive must open with steering lesson")
	lesson.lesson = ""
	lesson._start_aim()
	check(lesson.lesson == "shoot", "Protected aim must pause for the shot lesson")
	lesson.lesson = ""
	lesson.aim_left = 0.01
	lesson._tick_creature(0.02)
	check(lesson.phase == "aim" and lesson.aim_left > 1.0, "Protected missed window must recover")
	lesson.hull = 1.0
	lesson._damage(200.0)
	check(lesson.hull == 1.0 and not lesson.ended, "Protected lesson must survive mistakes")
	lesson.free()

	# Collision immunity prevents one overlapping rock taking repeated hull hits.
	var damage = fresh()
	damage._damage(24.0)
	damage._damage(24.0)
	check(damage.hull == 76.0, "Damage must honor temporary hit protection")
	damage.invulnerable = 0.0
	damage.boost = 2.0
	damage._damage(24.0)
	check(damage.hull == 76.0, "Boost must prevent collision damage")
	damage.free()
	var passage = fresh()
	passage.objects = [{"kind":"portal", "x":360.0, "y":936.0}]
	passage._move_objects(0.0, 260.0)
	check(passage.bonus_ride > 0.0, "Steering into a portal enters the safe bonus passage")
	passage._tick(1.0)
	check(passage.pickups > 0 and passage.travel == 0.0, "Bonus current grants salvage on its separate passage")
	passage._damage(500.0)
	check(passage.hull == passage.max_hull, "Bonus passage cannot damage the submarine")
	passage.free()

	# Early return retains collected rewards and explicitly drops completion bonus.
	var early = fresh(1)
	early.finished.connect(func(value: Dictionary): result = value)
	early.pickups = 27
	early.suspend()
	early._press(Vector2(250, 824))
	check(early.confirm_return and not early.ended, "Return early requires confirmation")
	early._press(Vector2(250, 850))
	check(not early.confirm_return and early.paused, "Cancel must keep world paused")
	early.confirm_return = true
	early._press(Vector2(250, 750))
	check(result.get("outcome") == "early" and result.get("pickups") == 27 and result.get("completion_bonus") == 0, "Early-return receipt must retain salvage")
	early.free()

	# Traverse every complete authored route with base gear and bounded steering.
	# The player policy follows visible pickups, avoids nearby rocks, then follows
	# the creature and dodges the warned stripe. No route timers are fast-forwarded.
	for route in range(3):
		var dive = fresh(route)
		dive.finished.connect(func(value: Dictionary): result = value)
		var saw_aim := false
		for frame in range(9000):
			var target_x: float = dive.ship_x
			if dive.phase == "travel":
				var nearest_y := -200.0
				for object in dive.objects:
					if object.kind == "salvage" and float(object.y) > nearest_y and float(object.y) < Dive.SHIP_Y + 30.0:
						nearest_y = float(object.y)
						target_x = float(object.x)
				for object in dive.objects:
					if object.kind == "rock" and absf(float(object.y) - Dive.SHIP_Y) < 130.0 and absf(float(object.x) - target_x) < 85.0:
						target_x = float(object.x) + (130.0 if float(object.x) < 360.0 else -130.0)
			elif dive.phase == "aim":
				saw_aim = true
				target_x = dive.creature_x
				dive._fire()
			elif dive.phase == "pursuit":
				target_x = dive.creature_x
				if dive.attack_warning > 0 or dive.attack_active > 0:
					target_x += -65.0 if dive.attack_x > dive.creature_x else 65.0
			dive.ship_x = move_toward(dive.ship_x, clampf(target_x, 90.0, 630.0), 500.0 / 60.0)
			dive._tick(1.0 / 60.0)
			if dive.ended:
				break
		check(saw_aim, "Route %d must transition to the final creature" % route)
		check(dive.caught and dive.ended, "Route %d must be catchable with base equipment" % route)
		check(result.get("completion_bonus", 0) > 0 and result.get("species") == Dive.SPECIES[route], "Each route needs its receipt and distinct recipe")
		check(dive.pickups > 0 and dive.elapsed < 110.0, "Authored route must retain salvage and finish in a short session")
		print("Route %d: %.1f seconds, %d salvage, %.0f hull" % [route + 1, dive.elapsed, dive.pickups, dive.hull])
		dive.free()
	print("Expedition: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
