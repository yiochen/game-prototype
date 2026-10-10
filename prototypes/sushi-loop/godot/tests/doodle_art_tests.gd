extends SceneTree
## Behavioral art contracts: centered feet, stable scale, six actual frames,
## exact connected cuts, and the deck-before-food occlusion boundary.

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
	session.advance(30.0)
	world.state = session.snapshot()
	root.add_child(world)
	world.update_layout()
	var art = world.art
	_expect(art.animations.size() >= 19, "Every playable character action and each conveyor cut has its own production loop")
	for clip in art.animations:
		var data: Dictionary = art.animations[clip]
		var frames: Array = data.frames
		_expect(frames.size() >= 6, clip + " contains at least six frames")
		var hashes := {}
		var fixed_scale := -1.0
		var registered := true
		var resolved := true
		for index in range(frames.size()):
			var key := str(frames[index])
			var texture: Texture2D = art.get_texture(key)
			if texture == null:
				resolved = false
				continue
			hashes[hash(texture.get_image().get_data())] = true
			var base := world.cell_base(4, 7)
			var fitted: Rect2 = art.fit(key, base, Vector2(90, 140))
			var anchor: Array = art.metadata[key].anchor
			registered = registered and (fitted.position + Vector2(anchor[0], anchor[1]) * fitted.size).is_equal_approx(base)
			var scale_value := fitted.size.x / texture.get_width()
			if fixed_scale < 0:
				fixed_scale = scale_value
			registered = registered and is_equal_approx(fixed_scale, scale_value)
			_expect(art.animation_frame(clip, (float(index) + 0.02) / float(data.fps)) == key, clip + " visits drawn frame " + str(index))
			if str(clip).begins_with("chef") or str(clip).begins_with("guest"):
				_expect(texture.get_height() >= 384, key + " keeps enough native pixels for phone rendering")
		_expect(resolved and hashes.size() == frames.size(), clip + " resolves genuinely different native pixel frames")
		_expect(registered, clip + " keeps its foot/deck anchor and physical scale through the loop")
		_expect(art.animation_frame(clip, (float(frames.size()) + 0.02) / float(data.fps)) == str(frames[0]), clip + " wraps back to its first frame")
	var clips := ["belt_end_left", "belt_horizontal", "belt_horizontal_b", "belt_end_right"]
	var belts: Array = []
	for object in world.state.objects:
		if object.kind == "belt":
			belts.append(object)
	var joins := true
	var selected := true
	for phase in range(6):
		var previous_end := Vector2.ZERO
		for quarter in range(4):
			var key := str(art.animations[clips[quarter]].frames[phase])
			var rect: Rect2 = art.fit(key, world.cell_base(belts[quarter].x, belts[quarter].y), Vector2(world.cell, world.cell * 2))
			if quarter > 0:
				joins = joins and is_equal_approx(rect.position.x, previous_end.x)
			previous_end = rect.end
			var region: Array = art.metadata[key].region
			joins = joins and int(region[0]) == quarter * 502 and int(region[2]) == 502
			selected = selected and world.belt_clip(belts[quarter]) == clips[quarter]
	_expect(joins, "All six phases fit their exact equal-width cuts edge to edge with no rail gaps")
	_expect(selected, "Neighbor topology selects the two caps and the two matching center cuts")
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
	_expect(dish_count == 4 and first_dish > last_belt, "A full conveyor draws every surface before any of its four dishes, including adjacent tiles")
	_expect(world.texture_filter == CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS, "Phone-sized sprites use smooth mipmapped sampling")
	var chef_frame: AtlasTexture = art.get_texture("chef_work_up_00")
	_expect(chef_frame.atlas.get_image().has_mipmaps(), "Native character source textures actually contain mipmaps")
	world.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: %s doodle animation and layering checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		quit(1)

func _expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)
