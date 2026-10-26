extends RefCounted
## The authored dark opening ends 178 source pixels above the 1248px root.
## Coordinates below are foot anchors in tile units, never sprite bounds.
const TRAVEL := 1.15
const CURTAIN_OFFSET := -0.95
const FADE_START := -0.55

static func enabled(floor_data: Dictionary) -> bool:
	return int(floor_data.get("backdrop_rows", 0)) == 3 and int(floor_data.get("entrance", {}).get("x", -1)) == 4 and int(floor_data.get("entrance", {}).get("y", -1)) == 3

static func anchor(customer: Dictionary, floor_data: Dictionary) -> Vector2i:
	return Vector2i(int(customer.get("door_lane", floor_data.entrance.x)), int(floor_data.entrance.y))

static func motion(direction: String, identity: String, random_state: int) -> Dictionary:
	# A separate entrance stream varies both crossings without consuming the
	# service RNG that chooses meals, seats and arrival times. Save the sample.
	var visual_random := RandomNumberGenerator.new()
	visual_random.seed = (identity + ":" + direction + ":" + str(random_state)).hash()
	return {"direction": direction, "distance": 0.0, "offset_x": visual_random.randf()}

static func present(visible: Dictionary, saved: Dictionary, speed: float) -> void:
	if not saved.has("door_motion"): return
	var motion: Dictionary = saved.door_motion
	var distance := float(motion.distance)
	var offset := -TRAVEL + distance if motion.direction == "enter" else -distance
	visible.y = float(saved.y) + offset
	# New visits use the nearest clear navigation lane, rather than converging
	# on the left tile. Keep the old interpolation for already-saved crossings.
	var lateral := float(motion.get("offset_x", 0.0))
	var outside_x := 4.0 + lateral if saved.has("door_lane") else float(saved.x) + lateral
	visible.x = lerpf(float(saved.x), outside_x, 1.0 - smoothstep(CURTAIN_OFFSET, 0.0, offset))
	visible.facing = "south" if motion.direction == "enter" else "north"
	visible.visual_phase = "walk"
	visible.visual_elapsed = distance / speed
	visible.doorway = true
	visible.door_alpha = smoothstep(-TRAVEL, FADE_START, offset)
	visible.door_light = lerpf(0.3, 1.0, visible.door_alpha)

static func valid(customer: Dictionary, floor_data: Dictionary) -> bool:
	if customer.has("door_lane"):
		var lane: Variant = customer.door_lane
		if not enabled(floor_data) or not (lane is int or lane is float) or not is_finite(float(lane)) or not float(lane) in [4.0, 5.0]: return false
	if customer.has("door_exit_offset"):
		var exit_offset: Variant = customer.door_exit_offset
		if not customer.has("door_lane") or not (exit_offset is int or exit_offset is float) or not is_finite(float(exit_offset)) or float(exit_offset) < 0.0 or float(exit_offset) > 1.0: return false
	if not customer.has("door_motion"): return true # Existing visits remain unchanged.
	var motion: Variant = customer.door_motion
	if not enabled(floor_data) or not motion is Dictionary: return false
	if not motion.get("direction") in ["enter", "exit"]: return false
	var lateral: Variant = motion.get("offset_x", 0.0)
	if not (lateral is float or lateral is int) or not is_finite(float(lateral)) or float(lateral) < 0.0 or float(lateral) > 1.0: return false
	var distance: Variant = motion.get("distance")
	if not (distance is float or distance is int) or not is_finite(float(distance)) or float(distance) < 0.0 or float(distance) >= TRAVEL: return false
	if customer.get("x") != anchor(customer, floor_data).x or customer.get("y") != floor_data.entrance.y: return false
	if customer.get("render_offset_x") != 0.0 or customer.get("render_offset_y") != 0.0: return false
	if motion.direction == "enter": return customer.get("phase") in ["walking", "entrance_wait"] and customer.get("meal_dish") == null and customer.get("first_dish_received") == false
	return customer.get("phase") == "leaving" and customer.get("visual_phase") == "walk" and customer.get("path", []) == [] and customer.get("navigation_mode") == "goal"
