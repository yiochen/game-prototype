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
	_expect(art.objects.size() == 28 and art.cell_size == 128.0, "The starter loads the approved 28-object subset at one 128px logical pitch")
	var verified_atlases := 0
	var verified_frames := 0
	for identity in art.objects:
		var object: Dictionary = art.objects[identity]
		for clip in object.clips:
			var action: Dictionary = object.clips[clip]
			for direction in action.directions:
				art.begin_frame()
				var entry: Dictionary = action.directions[direction]
				_expect(FileAccess.get_sha256(art.DIRECTORY + str(entry.image)) == entry.sha256, "%s/%s/%s ships the exact approved PNG bytes" % [identity, clip, direction])
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
	_expect(verified_atlases == 139 and verified_frames > 1300, "The audit exercises every selected atlas and directional frame")
	_expect(art.objects["coin-pop"].clips.pop.frames == 12 and art.objects["coin-pop"].clips.pop.loop == false, "Local sale feedback uses the approved twelve-frame native coin-pop one-shot")
	_test_connections(world)
	_expect(art.objects["entry-finished"].footprint == [4.0, 1.0], "The entrance preserves the approved four-tile footprint")
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

func _test_connections(world) -> void:
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

func _expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)
