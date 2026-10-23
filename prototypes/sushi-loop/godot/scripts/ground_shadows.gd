extends Node
## Native DirectionalLight3D shadows from hidden height/footprint proxies.
## The transparent receiver is composited below the unchanged color sprites.
const RECEIVER = preload("ground_shadow_receiver.gdshader")
const PRESENT = preload("ground_shadow_present.gdshader")
const RESOLUTION := 0.25
const LIGHT_DIRECTION := Vector3(0.55, -1.0, -0.35)
var viewport: SubViewport
var lighting_viewport: SubViewport
var presentation: Sprite2D
var scene: Node3D
var camera: Camera3D
var light: DirectionalLight3D
var receiver: MeshInstance3D
var boxes: MultiMeshInstance3D
var bodies: MultiMeshInstance3D
var _box_transforms: Array[Transform3D] = []
var _body_transforms: Array[Transform3D] = []
var _shapes: Dictionary = {}
var _view_geometry: Array = []
var _batch_uploads := 0
var _frames_submitted := 0
var _proxy_builds := 0
var count := 0
var cell := 256.0

func _ready() -> void:
	viewport = SubViewport.new()
	viewport.disable_3d = true
	viewport.transparent_bg = true
	viewport.gui_disable_input = true
	viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	lighting_viewport = SubViewport.new()
	lighting_viewport.own_world_3d = true
	lighting_viewport.gui_disable_input = true
	lighting_viewport.msaa_3d = Viewport.MSAA_2X
	lighting_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(lighting_viewport)
	presentation = Sprite2D.new()
	presentation.centered = false
	presentation.texture = lighting_viewport.get_texture()
	presentation.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var present_material := ShaderMaterial.new()
	present_material.shader = PRESENT
	presentation.material = present_material
	viewport.add_child(presentation)
	scene = Node3D.new()
	lighting_viewport.add_child(scene)
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	# White outside the floor becomes transparent in the presentation shader.
	environment.background_color = Color.WHITE
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.0
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world_environment.environment = environment
	scene.add_child(world_environment)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = 0.1
	camera.far = 25.0
	scene.add_child(camera)
	camera.current = true
	light = DirectionalLight3D.new()
	light.shadow_enabled = true
	light.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	light.directional_shadow_max_distance = 25.0
	light.shadow_bias = 0.015
	light.shadow_normal_bias = 0.25
	scene.add_child(light)
	light.look_at_from_position(Vector3.ZERO, LIGHT_DIRECTION)
	receiver = MeshInstance3D.new()
	receiver.mesh = PlaneMesh.new()
	receiver.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var receiver_material := ShaderMaterial.new()
	receiver_material.shader = RECEIVER
	receiver.material_override = receiver_material
	scene.add_child(receiver)
	boxes = _make_batch(BoxMesh.new())
	var capsule := CapsuleMesh.new()
	capsule.radius = 0.28
	capsule.height = 1.8
	capsule.radial_segments = 12
	capsule.rings = 4
	bodies = _make_batch(capsule)

func _make_batch(mesh: Mesh) -> MultiMeshInstance3D:
	var batch := MultiMeshInstance3D.new()
	batch.multimesh = MultiMesh.new()
	batch.multimesh.transform_format = MultiMesh.TRANSFORM_3D
	batch.multimesh.mesh = mesh
	batch.multimesh.visible_instance_count = 0
	batch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	scene.add_child(batch)
	return batch

func begin(dimensions: Vector2, cell_pitch := 256.0, floor_start := 0.0) -> void:
	set_active(true)
	var geometry := [dimensions, cell_pitch, floor_start]
	if geometry != _view_geometry:
		_view_geometry = geometry
		cell = cell_pitch
		viewport.size = Vector2i(maxi(1, ceili(dimensions.x * RESOLUTION)), maxi(1, ceili(dimensions.y * RESOLUTION)))
		lighting_viewport.size = viewport.size
		# Fit the allocated texture rectangle; the caller clips its padding.
		var extent := Vector2(viewport.size) / RESOLUTION / cell
		camera.size = extent.y
		var center := Vector3(extent.x * 0.5, 0, extent.y * 0.5)
		camera.look_at_from_position(center + Vector3(0, 20, 0), center, Vector3(0, 0, -1))
		var plane: PlaneMesh = receiver.mesh
		var start := clampf(floor_start / cell, 0.0, extent.y)
		plane.size = Vector2(extent.x, maxf(0.001, extent.y - start))
		receiver.position = Vector3(center.x, 0, (start + extent.y) * 0.5)
	_box_transforms.clear()
	_body_transforms.clear()
	count = 0

func set_active(active: bool) -> void:
	var mode := SubViewport.UPDATE_ALWAYS if active else SubViewport.UPDATE_DISABLED
	viewport.render_target_update_mode = mode
	lighting_viewport.render_target_update_mode = mode

func _box(shapes: Dictionary, dimensions: Vector3, center: Vector3) -> void:
	shapes.box.append(Transform3D(Basis.from_scale(dimensions), center))

func _proxy_shapes(identity: String) -> Dictionary:
	var family := "belt" if identity.begins_with("belt-") else "person" if identity.begins_with("customer-") or (identity.begins_with("chef-") and identity != "chef-blackboard") else identity
	if _shapes.has(family): return _shapes[family]
	var shapes := {"box": [], "body": []}
	if identity == "chef-blackboard":
		# Native Blender board occupies the front band, not the cell center.
		_box(shapes, Vector3(0.80, 0.67, 0.125), Vector3(0, 0.61, 0.40))
		for x in [-0.33, 0.33]:
			_box(shapes, Vector3(0.085, 0.98, 0.11), Vector3(x, 0.49, 0.355))
			_box(shapes, Vector3(0.13, 0.07, 0.21), Vector3(x, 0.035, 0.36))
	elif identity.begins_with("belt-") or identity == "stool-wood":
		var belt := identity.begins_with("belt-")
		var height := 0.76 if belt else 0.62
		var width := 1.0 if belt else 0.68
		_box(shapes, Vector3(width, 0.16, width), Vector3(0, height, 0))
		for x in [-1, 1]:
			for z in [-1, 1]:
				_box(shapes, Vector3(0.09, height, 0.09), Vector3(x * width * 0.36, height * 0.5, z * width * 0.36))
	elif family == "person":
		shapes.body.append(Transform3D(Basis.IDENTITY, Vector3(0, 0.9, 0)))
	else:
		_box(shapes, Vector3(0.72, 0.85, 0.72), Vector3(0, 0.425, 0))
	_shapes[family] = shapes
	_proxy_builds += 1
	return shapes

func add_caster(identity: String, ground: Vector2, pitch: float, direction: String) -> void:
	count += 1
	var angle: float = {"S": 0.0, "E": -PI * 0.5, "N": PI, "W": PI * 0.5}.get(direction, 0.0) if identity != "chef-blackboard" else 0.0
	var transform := Transform3D(Basis(Vector3.UP, angle).scaled(Vector3.ONE * pitch / cell), Vector3(ground.x / cell, 0, ground.y / cell))
	var shapes := _proxy_shapes(identity)
	for shape in shapes.box: _box_transforms.append(transform * shape)
	for shape in shapes.body: _body_transforms.append(transform * shape)

func _upload(batch: MultiMeshInstance3D, transforms: Array[Transform3D]) -> bool:
	var mesh := batch.multimesh
	var capacity := mesh.instance_count
	var resized := false
	if transforms.size() > capacity:
		capacity = maxi(16, int(pow(2, ceili(log(float(transforms.size())) / log(2.0)))))
		mesh.instance_count = capacity
		resized = true
	var previous: Array = batch.get_meta("transforms", [])
	if not resized and previous == transforms: return false
	# Upload all instance matrices in one buffer rather than issuing a rendering
	# server command for every leg/post. Unused capacity remains invisible.
	var buffer := PackedFloat32Array()
	buffer.resize(capacity * 12)
	var bounds := AABB()
	var local_bounds := mesh.mesh.get_aabb()
	for index in range(transforms.size()):
		var t := transforms[index]
		var instance_bounds := t * local_bounds
		bounds = instance_bounds if index == 0 else bounds.merge(instance_bounds)
		var offset := index * 12
		buffer[offset] = t.basis.x.x
		buffer[offset + 1] = t.basis.y.x
		buffer[offset + 2] = t.basis.z.x
		buffer[offset + 3] = t.origin.x
		buffer[offset + 4] = t.basis.x.y
		buffer[offset + 5] = t.basis.y.y
		buffer[offset + 6] = t.basis.z.y
		buffer[offset + 7] = t.origin.y
		buffer[offset + 8] = t.basis.x.z
		buffer[offset + 9] = t.basis.y.z
		buffer[offset + 10] = t.basis.z.z
		buffer[offset + 11] = t.origin.z
	# Supply bounds immediately; a new GPU instance buffer's automatic bounds
	# can arrive after its first shadow-culling pass in RenderingDevice renderers.
	mesh.custom_aabb = bounds
	mesh.buffer = buffer
	mesh.visible_instance_count = transforms.size()
	batch.set_meta("transforms", transforms.duplicate())
	_batch_uploads += 1
	return true

func finish() -> void:
	_upload(boxes, _box_transforms)
	_upload(bodies, _body_transforms)
	_frames_submitted += 1

func texture() -> Texture2D:
	return viewport.get_texture()

func diagnostics() -> Dictionary:
	return {"box_instances": boxes.multimesh.visible_instance_count, "body_instances": bodies.multimesh.visible_instance_count, "batch_uploads": _batch_uploads, "frames_submitted": _frames_submitted, "proxy_shapes_built": _proxy_builds, "batch_count": 2}
