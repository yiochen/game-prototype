extends SceneTree
## Verify the actual approved native frames, tile roots and compositing contract.

const World = preload("res://scripts/restaurant_view.gd")
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var world = World.new()
	world.size = Vector2(720, 1280)
	var session = Session.new_session(41)
	session.command({"type": "set_entrance_open", "open": false})
	session.advance(40.0)
	world.state = session.snapshot()
	root.add_child(world)
	world.update_layout()
	var art = world.art
	_expect(art.objects.size() == 34 and art.cell_size == 128.0, "The starter loads the approved 34-object subset at one 128px logical pitch")
	var verified_atlases := 0
	var verified_frames := 0
	for identity in art.objects:
		var object: Dictionary = art.objects[identity]
		for clip in object.clips:
			var action: Dictionary = object.clips[clip]
			for direction in action.directions:
				art.begin_frame()
				var entry: Dictionary = action.directions[direction]
				_expect(FileAccess.get_sha256(str(entry.get("_directory", art.DIRECTORY)) + str(entry.image)) == entry.sha256, "%s/%s/%s ships the exact approved PNG bytes" % [identity, clip, direction])
				var first: Dictionary = art.frame_data(identity, clip, direction)
				var image: Image = first.texture.get_image()
				_expect(image.has_mipmaps(), "%s/%s/%s imports real mipmaps for phone-scale sampling" % [identity, clip, direction])
				var distinct := {}
				var roots_fixed := true
				var mapped := true
				var base := Vector2(351, 644)
				var expected: Rect2 = art.registered_rect(identity, base, 90.0, clip, direction)
				var root_values: Array = first.root
				var source_scale := float(first.source_scale)
				var count := int(action.frames)
				for index in range(count):
					var data: Dictionary = art.frame_data(identity, clip, direction, (float(index) + 0.01) / float(action.fps))
					var region: Rect2 = data.region
					var pixels: Image = image.get_region(Rect2i(region))
					distinct[hash(pixels.get_data())] = true
					mapped = mapped and data.frame == index and region.size.is_equal_approx(Vector2(data.frame_size[0], data.frame_size[1]) * source_scale)
					roots_fixed = roots_fixed and (expected.position + Vector2(root_values[0], root_values[1]) * 90.0 / 128.0).is_equal_approx(base)
					roots_fixed = roots_fixed and expected.size.is_equal_approx(region.size * 90.0 / (128.0 * source_scale))
					verified_frames += 1
				_expect(mapped, "%s/%s/%s visits complete authored frames without cropping or resampling" % [identity, clip, direction])
				_expect(roots_fixed, "%s/%s/%s retains one ground root and uniform scale through every pose" % [identity, clip, direction])
				if count > 1:
					_expect(count >= 6 and distinct.size() >= 6, "%s/%s/%s has at least six genuinely different native frames" % [identity, clip, direction])
				if str(identity).begins_with("belt-"):
					_expect(count == 24 and distinct.size() == 24, identity + " keeps all 24 moving conveyor phases")
				var after: Dictionary = art.frame_data(identity, clip, direction, (float(count) + 0.01) / float(action.fps))
				_expect(after.frame == (count - 1 if action.get("loop", true) == false else 0), "%s/%s honors the authored one-shot or loop boundary" % [identity, clip])
				verified_atlases += 1
				art.end_frame()
	_expect(verified_atlases == 252 and verified_frames == 2860, "The audit exercises every selected atlas and directional frame")
	_expect(art.objects["coin-pop"].clips.pop.frames == 12 and art.objects["coin-pop"].clips.pop.loop == false, "Local sale feedback uses the approved twelve-frame native coin-pop one-shot")
	_expect(world.customer_clip({"phase": "waiting", "visual_phase": "seated-wait", "meal_dish": null}) == "seated-wait-empty", "Waiting customers have no meal sprite before consumption")
	_expect(world.customer_clip({"phase": "eating", "visual_phase": "eat", "meal_dish": {"recipe_id": "salmon_nigiri"}}) == "eat-salmon", "The actual consumed salmon dish chooses the native salmon eating clip")
	_expect(world.customer_clip({"phase": "leaving", "visual_phase": "stand-up", "meal_dish": null}) == "stand-up", "Meal variants retain the authored empty-handed stand-up transition")
	_test_visit_presentation(world)
	_test_connections(world)
	_test_rotatable_catalog(art)
	_expect(art.objects["backdrop-entrance"].footprint == [4.0, 3.0], "The entrance preserves the approved four-by-three-tile backdrop plane")
	_expect(art.objects["chef-blackboard"].facingPolicy == "single-player-facing" and art.objects["chef-blackboard"].clips.idle.directions.keys() == ["S"], "The blank front-band board has only its player-facing direction")
	_expect(world.texture_filter == CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS, "The shared renderer requests smooth mipmapped sampling at phone scale")
	art.begin_frame()
	art.frame_data("floor-cream")
	art.end_frame()
	_expect(art.sources.size() == 1, "Unused animation sources are released instead of keeping every atlas in mobile memory")
	world.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: %s approved art checks, %s atlases, %s whole frames" % [checks, verified_atlases, verified_frames])
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		quit(1)

func _test_visit_presentation(world) -> void:
	var active := {"phase": "waiting", "visual_phase": "seated-wait", "preferred_recipe_id": "cucumber_maki", "preference_phase": "active", "preference_phase_elapsed": 2.4, "preference_progress": 0.6}
	var feedback: Dictionary = world.customer_feedback(active)
	_expect(feedback.object == "bubble-preference" and feedback.clip == "cucumber-idle" and is_equal_approx(float(feedback.timer), 0.6), "Active preference shows the correct approved food bubble and saved circular timer progress")
	var pending := active.duplicate(true)
	pending.preference_phase = "pending"
	_expect(world.customer_feedback(pending).is_empty(), "Walking and sitting do not start an early visible preference cycle")
	var expired := active.duplicate(true)
	expired.preference_phase = "expired"
	expired.preference_phase_elapsed = 0.4
	feedback = world.customer_feedback(expired)
	_expect(feedback.clip == "cucumber-fade" and feedback.timer < 0, "Expiry fades the same food thought bubble once without a new timer")
	expired.preference_phase_elapsed = 3.4
	_expect(world.customer_feedback(expired).is_empty(), "A long-expired preference stays hidden while the next dish is accepted")
	var happy := {"phase": "eating", "visual_phase": "eat", "meal_dish": {"recipe_id": "salmon_nigiri"}, "preference_phase": "satisfied", "happy_elapsed": 0.3, "happy_duration": 2.2}
	feedback = world.customer_feedback(happy)
	_expect(feedback.object == "bubble-happy" and feedback.clip == "happy-smile-transition" and world.customer_pose_offset(happy, 128).y < 0, "A matching first dish shows the isolated ImageGen happy face and a brief whole-instance bounce")
	_expect(world.customer_clip(happy) == "eat-salmon", "Happiness retains the actual consumed food instead of swapping the character meal")
	happy.happy_elapsed = 1.7
	_expect(world.customer_feedback(happy).clip == "happy-smile-fade" and world.customer_pose_offset(happy, 128).is_zero_approx(), "The happy face fades after its brief bounce finishes")
	happy.preference_phase = "complete"
	_expect(world.customer_feedback(happy).is_empty(), "Later dishes do not restart the preference or happy bubble cycle")
	var restless := {"phase": "waiting", "visual_phase": "seated-wait", "restless": true}
	_expect(world.customer_clip(restless) == "restless", "An unfed restless guest uses its native empty-handed fidget action")
	restless.visual_phase = "stand-up"
	_expect(world.customer_clip(restless) == "stand-up", "Restlessness does not replace the authored leaving transition")
	_expect(world.chef_clip({"art_id": "chef-omar", "recipe_id": "cucumber_maki", "visual_phase": "hold", "active": true}) == "hold-cucumber", "Omar holds the correct approved cucumber plate")
	_expect(world.chef_clip({"art_id": "chef-omar", "recipe_id": "cucumber_maki", "visual_phase": "load", "active": true}) == "load-cucumber", "Omar's one-shot loading animation keeps cucumber food identity")
	_expect(world.chef_clip({"visual_phase": "work", "active": false}) == "idle" and world.activity_tint({"active": false}) != Color.WHITE, "Disconnected service uses a quiet idle treatment instead of an error badge")
	_expect(world.art.objects["bubble-happy"].clips.has("happy-smile-appear") and world.art.objects["bubble-happy"].clips.has("happy-smile-idle") and not world.art.objects["customer-rosa"].clips.has("happy"), "Smiling feedback extends the balloon without shipping unused native happy body actions")
	var passing := {"render_offset_x": 0.18, "render_offset_y": -0.12}
	_expect(world.customer_pose_offset(passing, 128).is_equal_approx(Vector2(0.18, -0.12) * 128), "Passing offsets are separate from the logical tile root and scale")
	world.reduced_motion = true
	happy.preference_phase = "satisfied"
	happy.happy_elapsed = 0.3
	_expect(world.customer_pose_offset(happy, 128).is_zero_approx(), "Reduced motion removes the brief bounce while preserving visit state")
	world.reduced_motion = false
	_expect(world.gallery_customers().size() == 7 and world.gallery_customers()[4].restless and world.gallery_customers()[5].phase == "entrance_wait" and world.gallery_customers()[6].navigation_mode == "wander", "The shared native gallery covers the original five visit moments plus puzzled admission and scared trapped guests")
	var doorstep := {"phase": "entrance_wait", "entrance_wait_elapsed": 0.4, "entrance_wait_total": 4.0}
	_expect(world.customer_clip(doorstep) == "stand" and world.customer_feedback(doorstep).object == "bubble-puzzled" and world.customer_feedback(doorstep).clip == "appear", "A new refused visitor stands with the approved puzzled bubble opening above their head")
	doorstep.entrance_wait_elapsed = 1.4
	_expect(world.customer_feedback(doorstep).clip == "idle" and is_equal_approx(float(world.customer_feedback(doorstep).seconds), 0.4), "A still-waiting visitor loops puzzled feedback from the saved entrance clock")
	doorstep.entrance_wait_elapsed = 3.4
	_expect(world.customer_feedback(doorstep).clip == "fade" and is_equal_approx(float(world.customer_feedback(doorstep).seconds), 0.4), "The puzzled balloon fades during the final second before a no-seat departure")
	var trapped := {"phase": "leaving", "navigation_mode": "wander", "wander_elapsed": 0.3, "preference_phase": "satisfied", "happy_elapsed": 0.3, "happy_duration": 2.2}
	_expect(world.customer_feedback(trapped).object == "bubble-panic" and world.customer_feedback(trapped).clip == "appear", "A trapped departing visitor shows scared feedback even when a recent meal would otherwise show happiness")
	trapped.wander_elapsed = 2.4
	_expect(world.customer_feedback(trapped).clip == "idle" and is_equal_approx(float(world.customer_feedback(trapped).seconds), 1.4), "A long-trapped visitor loops scared feedback without restarting its appearance")
	world.reduced_motion = true
	_expect(world.customer_feedback(doorstep).clip == "idle" and float(world.customer_feedback(doorstep).seconds) == 0.0 and world.customer_feedback(trapped).clip == "idle" and float(world.customer_feedback(trapped).seconds) == 0.0, "Reduced motion retains visible puzzled and scared symbols without opening, fading or animated pulses")
	world.reduced_motion = false

func _test_connections(world) -> void:
	var original: Dictionary = world.state
	world.state = original.duplicate(true)
	world.state.objects = []
	world.state.customers = []
	for index in range(4):
		world.state.objects.append({"id": "art-belt-%s" % index, "kind": "belt", "x": index + 1, "y": 8, "facing": "east", "travel_progress": 0.0, "dish": {"recipe_id": "salmon_nigiri"}})
	var art = world.art
	var belts: Array = []
	for object in world.state.objects:
		if object.kind == "belt":
			belts.append(object)
	var selected := true
	var joins := true
	for index in range(belts.size()):
		var identity: String = world.belt_clip(belts[index])
		selected = selected and identity == ["belt-start-e", "belt-straight-e", "belt-straight-e", "belt-end-e"][index]
		var base: Vector2 = world.cell_base(float(belts[index].x), float(belts[index].y))
		var deck: Vector2 = art.socket(identity, "deck") * world.cell / 128.0
		joins = joins and world.dish_base(belts[index]).is_equal_approx(base + deck)
		if index > 0:
			var previous: Dictionary = belts[index - 1]
			var previous_id: String = world.belt_clip(previous)
			var before: Array = art.objects[previous_id].ports.S.outgoing
			var after: Array = art.objects[identity].ports.S.incoming
			var before_point: Vector2 = world.cell_base(float(previous.x), float(previous.y)) + Vector2(before[0], before[1]) * world.cell / 128.0
			var after_point: Vector2 = base + Vector2(after[0], after[1]) * world.cell / 128.0
			joins = joins and before_point.is_equal_approx(after_point)
	_expect(selected, "Neighbor topology selects the approved start cap, two middle modules and end cap")
	_expect(joins, "Native ports meet exactly at one tile pitch, and dishes rest on the registered deck socket")
	var last_belt := -1
	var first_dish := 10000
	var dish_count := 0
	var plan: Array = world.render_plan()
	for index in range(plan.size()):
		if plan[index].kind == "belt":
			last_belt = index
		elif plan[index].kind == "dish":
			first_dish = mini(first_dish, index)
			dish_count += 1
	_expect(dish_count == 4 and first_dish > last_belt, "Every connected belt surface is drawn before every carried plate")
	world.state = original

func _test_rotatable_catalog(art) -> void:
	for identity in ["belt-start-e", "belt-straight-e", "belt-end-e", "stool-wood", "plant-angular", "barrel-wood", "crate-wood", "lantern-gold"]:
		var all_directions := true
		for clip in art.objects[identity].clips.values():
			for direction in ["N", "E", "S", "W"]:
				all_directions = all_directions and clip.directions.has(direction)
		_expect(all_directions, identity + " has authored frames for all four editor rotations, without a South fallback")
	# The belt-e family is rotated in native capture space. Its South capture
	# transports east; cardinal object facing is not the capture label.
	var flows := {
		"east": {"capture": "S", "step": Vector2(128, 0)},
		"north": {"capture": "E", "step": Vector2(0, -128)},
		"west": {"capture": "N", "step": Vector2(-128, 0)},
		"south": {"capture": "W", "step": Vector2(0, 128)},
	}
	for facing in flows:
		var capture: String = flows[facing].capture
		var step: Vector2 = flows[facing].step
		var joined := true
		var timing := true
		var deck: Vector2 = art.socket("belt-straight-e", "deck", capture)
		var ids := ["belt-start-e", "belt-straight-e", "belt-end-e"]
		for index in range(ids.size()):
			var identity: String = ids[index]
			var action: Dictionary = art.clip_data(identity, "running")
			timing = timing and action.frames == 24 and action.fps == 12 and action.loop == true
			joined = joined and art.socket(identity, "deck", capture).is_equal_approx(deck)
			if index > 0:
				var previous: Array = art.objects[ids[index - 1]].ports[capture].outgoing
				var incoming: Array = art.objects[identity].ports[capture].incoming
				joined = joined and (Vector2(previous[0], previous[1]) - Vector2(incoming[0], incoming[1])).is_equal_approx(step)
		_expect(joined, facing + " conveyor capture ports join at exactly one grid pitch with a shared deck root")
		_expect(timing, facing + " conveyor captures keep the synchronized native 24-frame transport loop")

func _expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)
