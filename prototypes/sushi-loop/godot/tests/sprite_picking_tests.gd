extends SceneTree
## The rendered, registered atlas silhouette is the editor's selection surface.
## Run through tools/test_native.py; gesture probes use isolated real save data.
const World = preload("res://scripts/restaurant_view.gd")
const ArtBook = preload("res://scripts/art_book.gd")
const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var checks := 0
var failures: Array[String] = []
var images: Dictionary = {}
var probes: Dictionary = {}

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Run sprite_picking_tests.gd through tools/test_native.py for isolated save storage.")
		quit(1)
		return
	var requested := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(requested[0]), int(requested[1])) if requested.size() == 2 else Vector2i(720, 1280)
	var world = World.new()
	root.add_child(world)
	world.size = Vector2(720, 1280)
	world.state = Session.new_session(41).snapshot()
	world.state.customers = []
	world.state.mode = "edit"
	world.update_layout()
	_test_mask_frames_and_cache()
	_test_extrusion_and_rotation(world)
	_test_painter_order_and_blockers(world)
	_test_attachments(world)
	_test_camera_and_clips(world)
	world.queue_free()
	await _frames()
	await _test_app_gestures()
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty():
		DirAccess.make_dir_recursive_absolute(destination)
		var report := FileAccess.open(destination.path_join("sprite-probes.json"), FileAccess.WRITE)
		report.store_string(JSON.stringify(probes, "  ") + "\n")
	images.clear()
	await create_timer(0.1).timeout
	print("Sprite picking probes: " + JSON.stringify(probes))
	if failures.is_empty():
		print("PASS: %s sprite picking checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		printerr("%s of %s sprite picking checks failed" % [failures.size(), checks])
		quit(1)

func _expect(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func _object(state: Dictionary, identity: String) -> Dictionary:
	for object in state.objects:
		if str(object.id) == identity: return object
	return {}

func _fixture(world, objects: Array, customers: Array = []) -> void:
	world.state.objects = objects.duplicate(true)
	world.state.customers = customers.duplicate(true)
	world.state.camera = {"x": 0.0, "y": 0.0}
	world.state.elapsed = 0.0
	world.editor_preview.clear()
	world.update_layout()

func _image(record: Dictionary) -> Image:
	var texture: Texture2D = record.texture
	var identity := texture.get_instance_id()
	if not images.has(identity):
		var pixels := texture.get_image()
		if pixels.is_compressed(): pixels.decompress()
		images[identity] = pixels
	return images[identity]

func _alpha(record: Dictionary, point: Vector2) -> float:
	var bounds: Rect2 = record.rect
	if not bounds.has_point(point): return 0.0
	var region: Rect2 = record.region
	var pixel := Vector2i((point - bounds.position) / bounds.size * region.size + region.position)
	var pixels := _image(record)
	if pixel.x < 0 or pixel.y < 0 or pixel.x >= pixels.get_width() or pixel.y >= pixels.get_height(): return 0.0
	return pixels.get_pixelv(pixel).a * float(record.tint.a)

func _raw_owner(world, point: Vector2) -> String:
	# Independent source-image alpha oracle; does not call ArtBook's BitMap API.
	var records: Array = world.sprite_hits()
	for index in range(records.size() - 1, -1, -1):
		var record: Dictionary = records[index]
		if _alpha(record, point) > 0.1: return str(record.owner_id)
	return ""

func _record(world, owner: String, art_id: String) -> Dictionary:
	for record in world.sprite_hits():
		if str(record.owner_id) == owner and str(record.art_id) == art_id: return record
	return {}

func _point(world, owner: String, art_id := "", above := INF, app = null) -> Vector2:
	for record in world.sprite_hits():
		if str(record.owner_id) != owner or (not art_id.is_empty() and str(record.art_id) != art_id): continue
		var region: Rect2 = record.region
		var bounds: Rect2 = record.rect
		var pixels := _image(record)
		for y in range(2, int(region.size.y), 5):
			for x in range(2, int(region.size.x), 5):
				var pixel := Vector2i(region.position) + Vector2i(x, y)
				if pixels.get_pixelv(pixel).a < 0.8: continue
				var point := bounds.position + (Vector2(x, y) + Vector2(0.5, 0.5)) / region.size * bounds.size
				if point.y >= above or not world.portrait.has_point(point): continue
				if app != null and not app._floor_drop(point): continue
				if _raw_owner(world, point) == owner: return point
	return Vector2(INF, INF)

func _overlap(world, back: Dictionary, front: Dictionary, front_opaque: bool) -> Vector2:
	if back.is_empty() or front.is_empty(): return Vector2(INF, INF)
	var shared: Rect2 = back.rect.intersection(front.rect).intersection(world.portrait)
	for y in range(int(shared.position.y) + 1, int(shared.end.y), 2):
		for x in range(int(shared.position.x) + 1, int(shared.end.x), 2):
			var point := Vector2(x, y)
			if _alpha(back, point) < 0.8: continue
			var front_alpha := _alpha(front, point)
			if (front_alpha < 0.8 if front_opaque else front_alpha > 0.02): continue
			var expected: String = str(front.owner_id) if front_opaque else str(back.owner_id)
			if _raw_owner(world, point) == expected: return point
	return Vector2(INF, INF)

func _test_mask_frames_and_cache() -> void:
	var art = ArtBook.new()
	var path := "fixture:animated-alpha.png"
	var pixels := Image.create(8, 4, false, Image.FORMAT_RGBA8)
	pixels.fill(Color(1, 1, 1, 0.02))
	pixels.set_pixel(1, 1, Color.WHITE)
	pixels.set_pixel(7, 3, Color.WHITE)
	var texture := ImageTexture.create_from_image(pixels)
	art.sources[path] = texture
	art.objects.fixture = {"frameSize": [4, 4], "root": [2, 2], "clips": {"move": {"fps": 2, "loop": true, "frames": 2, "directions": {"S": {"image": "animated-alpha.png", "_directory": "fixture:", "rects": [[0, 0, 4, 4], [4, 0, 4, 4]]}}}}}
	var first: Dictionary = art.frame_data("fixture", "move", "S", 0.0)
	var second: Dictionary = art.frame_data("fixture", "move", "S", 0.6)
	var looped: Dictionary = art.frame_data("fixture", "move", "S", 1.1)
	_expect(first.frame == 0 and second.frame == 1 and looped.frame == 0 and first.region != second.region, "Animated picking resolves the current atlas region and wraps with the rendered clip")
	_expect(art.frame_has_ink(first, Vector2(1.5, 1.5)) and not art.frame_has_ink(first, Vector2(0.5, 0.5)) and not art.frame_has_ink(first, Vector2(-1, 1)) and not art.frame_has_ink(first, Vector2(8, 1)), "Alpha masks reject transparent padding, sub-threshold alpha and out-of-atlas coordinates")
	_expect(not art.frame_has_ink(second, second.region.position + Vector2(1.5, 1.5)) and art.frame_has_ink(second, second.region.position + Vector2(3.5, 3.5)), "Animation frames sample atlas offsets rather than reusing the first frame's silhouette")
	var mask: BitMap = art.alpha_masks[path].mask
	art.frame_has_ink(first, Vector2(1.5, 1.5))
	_expect(art.alpha_masks.size() == 1 and art.alpha_masks[path].mask == mask, "Repeated queries reuse one compact mask for the loaded atlas")
	var replacement := Image.create(8, 4, false, Image.FORMAT_RGBA8)
	replacement.fill(Color.TRANSPARENT)
	replacement.set_pixel(2, 2, Color.WHITE)
	art.sources[path] = ImageTexture.create_from_image(replacement)
	var reloaded: Dictionary = art.frame_data("fixture", "move", "S", 0.0)
	_expect(not art.frame_has_ink(reloaded, Vector2(1.5, 1.5)) and art.frame_has_ink(reloaded, Vector2(2.5, 2.5)) and art.alpha_masks[path].mask != mask, "Replacing a texture at the same path invalidates its old alpha mask")
	art.begin_frame()
	art.end_frame()
	_expect(art.sources.is_empty() and art.alpha_masks.is_empty(), "Atlas eviction releases its CPU alpha mask with the texture")
	art.reload()
	_expect(art.alpha_masks.is_empty(), "Catalog reload cannot retain stale hit masks")

func _test_extrusion_and_rotation(world) -> void:
	var chef := _object(Session.new_session(41).snapshot(), "chef-1").duplicate(true)
	chef.merge({"x": 3, "y": 5, "facing": "south", "visual_phase": "idle"}, true)
	_fixture(world, [chef])
	var base: Vector2 = world.cell_base(3, 5)
	var head := _point(world, "chef-1", "chef-lena", base.y - world.cell * 0.5)
	_expect(head.is_finite() and world.object_at(head).get("id") == "chef-1", "An opaque chef hat above its ground tile selects the chef under the visible pixels")
	_expect(head.is_finite() and floori((head.y - world.floor_origin.y) / world.cell) < 5, "The chef probe really lies in a different screen tile from its ground anchor")
	probes.chef_hat = str(head)
	var plant := {"id": "plant", "kind": "decor", "art_id": "plant-angular", "x": 3, "y": 5, "facing": "east"}
	_fixture(world, [plant])
	var leaf := _point(world, "plant", "plant-angular", base.y - world.cell * 0.5)
	_expect(leaf.is_finite() and world.object_at(leaf).get("id") == "plant", "A leaf above a plant's ground cell selects its actual owner")
	var east := _record(world, "plant", "plant-angular")
	world.state.objects[0].facing = "west"
	var west := _record(world, "plant", "plant-angular")
	_expect(east.direction == "E" and west.direction == "W" and east.source_path != west.source_path, "Rotating a prop immediately replaces its directional hit frame before drawing")
	var changed := Vector2(INF, INF)
	var old_bounds: Rect2 = east.rect
	for y in range(int(old_bounds.position.y) + 1, int(old_bounds.end.y), 2):
		for x in range(int(old_bounds.position.x) + 1, int(old_bounds.end.x), 2):
			var point := Vector2(x, y)
			if world.portrait.has_point(point) and _alpha(east, point) > 0.8 and _alpha(west, point) < 0.02 and _raw_owner(world, point).is_empty(): changed = point; break
		if changed.is_finite(): break
	_expect(changed.is_finite() and world.object_at(changed).is_empty(), "A rotated plant no longer selects opaque pixels belonging only to its old facing")
	probes.plant_old_leaf_now_gap = str(changed)
	var gap := Vector2(INF, INF)
	var bounds: Rect2 = west.rect
	for y in range(int(bounds.position.y) + 1, int(bounds.end.y), 3):
		for x in range(int(bounds.position.x) + 1, int(bounds.end.x), 3):
			var candidate := Vector2(x, y)
			if world.portrait.has_point(candidate) and _alpha(west, candidate) < 0.02 and _raw_owner(world, candidate).is_empty(): gap = candidate; break
		if gap.is_finite(): break
	_expect(gap.is_finite() and world.object_at(gap).is_empty(), "Transparent padding inside a registered plant rectangle cannot select the ground-tile owner")
	probes.plant_transparent_padding = str(gap)

func _test_painter_order_and_blockers(world) -> void:
	var seat := {"id": "back-seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"}
	var chef := _object(Session.new_session(41).snapshot(), "chef-1").duplicate(true)
	chef.merge({"x": 3, "y": 6, "facing": "south", "visual_phase": "idle"}, true)
	_fixture(world, [chef, seat]) # Intentionally reverse state order.
	var back := _record(world, "back-seat", "stool-wood")
	var front := _record(world, "chef-1", "chef-lena")
	var opaque := _overlap(world, back, front, true)
	var clear := _overlap(world, back, front, false)
	_expect(opaque.is_finite() and world.object_at(opaque).get("id") == "chef-1", "Painter-depth order selects the front chef over an opaque overlapping stool regardless of state order")
	_expect(clear.is_finite() and world.object_at(clear).get("id") == "back-seat", "Transparent pixels of a front sprite fall through to the visible owned object behind it")
	probes.overlap_front = str(opaque)
	probes.overlap_transparent = str(clear)
	var visitor := {"id": "visitor", "art_id": "customer-rosa", "x": 3, "y": 5, "facing": "south", "phase": "waiting", "visual_phase": "seated-wait-empty", "render_offset_y": 0.0, "elapsed": 0.0, "preference_phase": "active", "preferred_recipe": "salmon_nigiri", "restless": false}
	_fixture(world, [seat], [visitor])
	back = _record(world, "back-seat", "stool-wood")
	front = _record(world, "", "customer-rosa")
	opaque = _overlap(world, back, front, true)
	_expect(opaque.is_finite() and world.object_at(opaque).is_empty(), "An opaque noneditable customer's body blocks the stool hidden behind it")
	probes.guest_blocker = str(opaque)
	# A deliberately hidden owned seat at the fixed border is a renderer fixture,
	# never persisted as a legal edit; room props must block it just like guests.
	seat.x = -0.5
	seat.y = 3
	_fixture(world, [seat])
	back = _record(world, "back-seat", "stool-wood")
	var room_point := Vector2(INF, INF)
	for candidate in world.sprite_hits():
		if str(candidate.owner_id).is_empty() and str(candidate.art_id) == "wall-middle":
			var point := _overlap(world, back, candidate, true)
			if point.is_finite(): room_point = point; break
	_expect(room_point.is_finite() and world.object_at(room_point).is_empty(), "Opaque fixed wall art blocks selection of an owned object hidden behind it")
	probes.room_blocker = str(room_point)

func _test_attachments(world) -> void:
	var chef := _object(Session.new_session(41).snapshot(), "chef-1").duplicate(true)
	chef.merge({"x": 3, "y": 5, "facing": "north", "visual_phase": "idle"}, true)
	_fixture(world, [chef])
	for art_id in ["chef-blackboard", "dish-salmon"]:
		var point := _point(world, "chef-1", art_id)
		_expect(point.is_finite() and world.object_at(point).get("id") == "chef-1", "The chef's %s attachment selects its owning chef" % art_id)
		probes[art_id] = str(point)
	var belt := {"id": "belt", "kind": "belt", "x": 3, "y": 5, "facing": "east", "travel_progress": 0.0, "dish": {"recipe_id": "salmon_nigiri"}}
	var next := {"id": "next-belt", "kind": "belt", "x": 4, "y": 5, "facing": "east", "travel_progress": 0.0, "dish": null}
	_fixture(world, [belt, next])
	var before := _record(world, "belt", "dish-salmon")
	var dish := _point(world, "belt", "dish-salmon")
	_expect(dish.is_finite() and world.object_at(dish).get("id") == "belt", "A plate resting on the belt selects the owning conveyor")
	world.state.objects[0].travel_progress = 0.75
	world.state.elapsed = 0.45
	var after := _record(world, "belt", "dish-salmon")
	var moving := _point(world, "belt", "dish-salmon")
	_expect(after.rect.position.is_equal_approx(before.rect.position + Vector2.RIGHT * world.cell * 0.75) and moving.is_finite() and world.object_at(moving).get("id") == "belt", "A plate between neighboring modules follows its moving registered position while retaining its original belt owner")
	probes.moving_dish = str(moving)
	var belt_frame := _record(world, "belt", "belt-start-e")
	_expect(belt_frame.frame > 0, "Animated conveyor hit records track the current rendered belt frame")

func _test_camera_and_clips(world) -> void:
	var plant := {"id": "plant", "kind": "decor", "art_id": "plant-angular", "x": 3, "y": 5, "facing": "east"}
	_fixture(world, [plant])
	var point := _point(world, "plant")
	world.state.camera = {"x": 0.35, "y": 0.25}
	var shifted: Vector2 = point - Vector2(0.35, 0.25) * world.cell
	_expect(world.object_at(shifted).get("id") == "plant", "A camera change invalidates hit geometry immediately without waiting for a rendered frame")
	world.size = Vector2(1280, 720)
	world.update_layout()
	var narrow := _point(world, "plant")
	_expect(narrow.is_finite() and world.object_at(narrow).get("id") == "plant", "Landscape resizing rebuilds the sprite's registered hit rectangle at the new tile pitch")
	_expect(world.object_at(Vector2(world.portrait.position.x - 1, narrow.y)).is_empty() and world.object_at(Vector2(world.portrait.end.x + 1, narrow.y)).is_empty() and world.object_at(Vector2(-1, narrow.y)).is_empty(), "Letterbox and Control bounds cannot select extruded off-portrait sprite pixels")
	world.show_gallery = true
	_expect(world.object_at(narrow).is_empty() and world.sprite_hits().is_empty(), "Gallery display disables restaurant ownership picking")
	world.show_gallery = false

func _test_app_gestures() -> void:
	var app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await _frames()
	app.session = Session.new_session(41)
	app._editor_command({"type": "set_mode", "mode": "edit"})
	var moved: Dictionary = app._editor_command({"type": "editor_move", "id": "chef-1", "x": 1, "y": 3})
	_expect(moved.get("ok", false), "The head-drag regression uses a legal public editor move, not synthetic controller state")
	app._editor_command({"type": "editor_select", "id": null})
	app._refresh()
	app._layout()
	await _frames()
	# Keep the hat visible above its below-object tools in tall and short windows.
	var camera_y: float = maxf(0.0, (app.world.floor_origin.y + 3.5 * app.world.cell - 360.0) / app.world.cell)
	app.session.command({"type": "set_camera", "x": 0.0, "y": camera_y})
	app._refresh()
	await _frames()
	var ground: Vector2 = app.world.cell_base(1, 3)
	var head := _point(app.world, "chef-1", "chef-lena", ground.y - app.world.cell * 0.5, app)
	_expect(head.is_finite() and app._object_at(head).get("id") == "chef-1", "The actual app controller delegates a visible raised hat to renderer picking")
	if not head.is_finite():
		app.queue_free()
		await _frames()
		return
	var saved_position: Vector2 = app.world.position
	var saved_scale: Vector2 = app.world.scale
	app.world.position += Vector2(7, 11)
	app.world.scale = Vector2(0.85, 0.9)
	var transformed: Vector2 = app.get_global_transform().affine_inverse() * app.world.get_global_transform() * head
	_expect(app._object_at(transformed).get("id") == "chef-1", "Root-to-world conversion honors the actual translated and scaled CanvasItem transform")
	app.world.position = saved_position
	app.world.scale = saved_scale
	await _touch(app, head, true)
	await _drag(app, head, head - Vector2(app.world.cell, 0))
	await _touch(app, head - Vector2(app.world.cell, 0), false)
	_expect(int(_object(app.session.snapshot(), "chef-1").x) == 1 and str(app.session.snapshot().editor.selected_id).is_empty() and float(app.session.snapshot().camera.x) > 0, "The first drag on a visible unselected hat still pans without selecting or moving the chef")
	app.session.command({"type": "set_camera", "x": 0.0, "y": camera_y})
	app._refresh()
	await _frames()
	head = _point(app.world, "chef-1", "chef-lena", ground.y - app.world.cell * 0.5, app)
	await _capture(app, "01-hat-before-selection")
	await _touch(app, head, true)
	await _touch(app, head, false)
	await _capture(app, "02-hat-selected")
	_expect(app.session.snapshot().editor.selected_id == "chef-1", "A short tap on the same visible hat selects the actual chef")
	var finish: Vector2 = head + Vector2(app.world.cell, 0)
	await _touch(app, head, true)
	_expect(app.gesture_kind == "object" and app.gesture_grab_offset.y < -0.5, "Beginning a selected head drag captures its above-ground grab offset in tile units")
	await _drag(app, head, finish)
	await _capture(app, "03-hat-drag-preview")
	_expect(app.world.editor_preview.get("x") == 2 and app.world.editor_preview.get("y") == 3 and app.world.editor_preview.get("valid", false), "The head-drag preview moves the ground root by one tile without snapping it to the pointer's upper tile")
	await _touch(app, finish, false)
	await _capture(app, "04-hat-moved-one-tile")
	var chef := _object(app.session.snapshot(), "chef-1")
	_expect(int(chef.x) == 2 and int(chef.y) == 3 and app.session.snapshot().editor.selected_id == "chef-1" and app.gesture_grab_offset.is_zero_approx(), "Releasing the head drag commits exactly one ground tile and clears the gesture offset")
	var snapshot: Dictionary = app.session.save_data()
	var beige: Vector2 = app.editor_ui.inventory_backing.get_global_rect().end - Vector2(3, 80) * app.editor_ui.unit
	await _touch(app, beige, true)
	await _drag(app, beige, beige + Vector2(app.world.cell, 0))
	await _touch(app, beige + Vector2(app.world.cell, 0), false)
	_expect(app.session.save_data() == snapshot and app.pointer == -1 and app.armed_item.is_empty(), "The cream inventory backdrop retains native input ownership and cannot pick or drag sprites behind it")
	var empty: Vector2 = app.world.cell_base(5, 3)
	_expect(app.world.object_at(empty).is_empty(), "The deselection probe lands on an actually empty rendered floor pixel")
	await _touch(app, empty, true)
	await _touch(app, empty, false)
	_expect(str(app.session.snapshot().editor.selected_id).is_empty(), "An empty floor tap deselects rather than selecting an object's invisible ground rectangle")
	probes.native_hat_source = str(head)
	probes.native_hat_destination = str(finish)
	probes.native_canvas_size = str(app.size)
	app.queue_free()
	await _frames()

func _capture(app, name: String) -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	DirAccess.make_dir_recursive_absolute(destination)
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	_expect(image.save_png(destination.path_join(name + ".png")) == OK, "The actual native %s view exports review pixels" % name)

func _frames(count := 3) -> void:
	for index in range(count): await process_frame

func _touch(app, point: Vector2, down: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.position = app.get_viewport_transform() * point
	event.index = 29
	event.pressed = down
	Input.parse_input_event(event)
	await _frames(2)

func _drag(app, from: Vector2, to: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.position = app.get_viewport_transform() * to
	event.relative = app.get_viewport_transform().basis_xform(to - from)
	event.index = 29
	Input.parse_input_event(event)
	await _frames(2)
