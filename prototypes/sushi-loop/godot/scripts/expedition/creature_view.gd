extends RefCounted
## Issue #23: the approved Storm Eel as live 3D (one skinned GLB with named
## clips), rendered into its own transparent SubViewport and drawn by the
## expedition view between the seabed and the ship.
##
## The camera matches the character contract (ordinary orthographic, 35°
## elevation, seven columns across) and is offset so the eel's ground root
## lands on its 2D route cell; the body reads `BODY_ROW_OFFSET` rows north of
## that root. Lighting is flat (mostly ambient plus a soft key) with the
## ART-05 135% contrast. The organs' glow is driven per clip here, not baked.
## Gameplay never reads the animation: the hit area is a fixed rule ellipse.
const MODEL := "res://assets/expedition/creature/storm-eel.glb"
const ELEVATION := deg_to_rad(35.0)
## Rest-body centre (0.78 above ground, 0.3 south of the root) projected onto screen rows.
const BODY_ROW_OFFSET := 0.47
const LOOPS := ["swim", "restless", "hooked", "struggle", "exhausted"]
## Spine order from the snout back: hook positions and shadows follow these.
const BODY_BONES := ["head", "spine_00", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "spine_06",
	"spine_07", "spine_08", "spine_09", "spine_10", "spine_11", "spine_12", "spine_13"]

var viewport: SubViewport
var camera: Camera3D
var model: Node3D
var player: AnimationPlayer
var skeleton: Skeleton3D
var spot_materials: Array[StandardMaterial3D] = []
var body_materials: Array[StandardMaterial3D] = []
var clip := ""
var clip_time := 0.0
var flash := 0.0
var _bone_ids: Dictionary = {}
var _scale := 1.0

func _init(host: Node) -> void:
	viewport = SubViewport.new()
	viewport.own_world_3d = true
	viewport.transparent_bg = true
	viewport.msaa_3d = Viewport.MSAA_2X
	viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	host.add_child(viewport)
	var environment := Environment.new()
	environment.background_mode = Environment.BG_CLEAR_COLOR
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.82
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	environment.adjustment_enabled = true
	environment.adjustment_contrast = 1.35
	var world := WorldEnvironment.new(); world.environment = environment; viewport.add_child(world)
	var key := DirectionalLight3D.new()
	key.light_energy = 0.5
	key.rotation = Vector3(deg_to_rad(-62.0), deg_to_rad(-25.0), 0.0)
	viewport.add_child(key)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	camera.rotation = Vector3(-ELEVATION, 0.0, 0.0)
	camera.near = 0.1; camera.far = 100.0
	viewport.add_child(camera)
	model = (load(MODEL) as PackedScene).instantiate()
	viewport.add_child(model)
	player = model.find_child("AnimationPlayer", true, false)
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for name in player.get_animation_list():
		player.get_animation(name).loop_mode = Animation.LOOP_LINEAR if name in LOOPS else Animation.LOOP_NONE
	skeleton = model.find_children("*", "Skeleton3D", true, false)[0]
	for i in range(BODY_BONES.size()): _bone_ids[BODY_BONES[i]] = skeleton.find_bone(BODY_BONES[i])
	for node in model.find_children("*", "MeshInstance3D", true, false): _flatten(node)
	play("swim", 0.0)

## Flat-lit faceted materials keeping the authored colours.
func _flatten(mesh: MeshInstance3D) -> void:
	for surface in range(mesh.mesh.get_surface_count()):
		var source := mesh.get_active_material(surface) as BaseMaterial3D
		var material := StandardMaterial3D.new()
		material.resource_name = source.resource_name if source != null else ""
		material.albedo_color = source.albedo_color if source != null else Color.WHITE
		material.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT
		material.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
		material.roughness = 1.0; material.metallic = 0.0
		material.emission_enabled = true
		var spot := material.resource_name == "eel_spot"
		material.emission = source.emission if spot and source != null else Color.WHITE
		material.emission_energy_multiplier = 1.0 if spot else 0.0
		(spot_materials if spot else body_materials).append(material)
		mesh.set_surface_override_material(surface, material)

func play(name: String, blend := 0.25) -> void:
	if name == clip or not player.has_animation(name): return
	player.play(name, blend)
	clip = name; clip_time = 0.0
	if name == "hit": flash = 0.14

func finished() -> bool: return not player.is_playing() or (clip not in LOOPS and clip_time >= player.current_animation_length)

## Organ glow per clip (seconds into the clip -> emission energy).
func _glow() -> float:
	var t := clip_time
	match clip:
		"swim": return 0.9 + 0.15 * sin(t * 3.0)
		"restless": return 1.1 + 0.9 * maxf(0.0, sin(t * 14.0))
		"hit": return 0.15 if t < 0.25 else 0.8
		"hooked": return 0.9 + 0.3 * sin(t * 8.0)
		"struggle": return 1.1 + 0.5 * maxf(0.0, sin(t * 10.0))
		"exhausted": return 0.35 + 0.1 * sin(t * 2.0)
		"escape": return 1.4
		# Issue #25 discharge: charging up, then crackling while it strikes.
		"windup": return 1.0 + minf(1.0, t / 1.4) * 1.6 + 0.4 * sin(t * 22.0)
		"attack": return 2.6 + 0.8 * sin(t * 40.0)
	return 1.0

## Advance the animation and place the camera so the ground root lands on
## `root` (view coordinates) of a `view_size` view with `cell` per column.
## `physical` is the view's on-screen scale, for a crisp render target.
func frame(delta: float, root: Vector2, view_size: Vector2, cell: float, physical: float) -> void:
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_scale = physical
	var pixels := Vector2i(maxi(1, int(round(view_size.x * physical))), maxi(1, int(round(view_size.y * physical))))
	if viewport.size != pixels: viewport.size = pixels
	camera.size = view_size.x / cell
	var offset := (root - view_size * 0.5) / cell
	var back := Vector3(0.0, sin(ELEVATION), cos(ELEVATION))
	var up := Vector3(0.0, cos(ELEVATION), -sin(ELEVATION))
	camera.position = back * 30.0 - Vector3.RIGHT * offset.x + up * offset.y
	player.advance(delta)
	clip_time += delta
	flash = maxf(0.0, flash - delta)
	var glow := _glow()
	for material in spot_materials: material.emission_energy_multiplier = glow
	for material in body_materials: material.emission_energy_multiplier = 0.04 if flash > 0.0 else 0.0

## Catch cutscene pose: grown and turned about its ground root (1, 0 at rest).
func pose(scale_value: float, yaw: float) -> void:
	model.scale = Vector3.ONE * scale_value
	model.rotation.y = yaw

func stop_rendering() -> void:
	viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED

func texture() -> Texture2D: return viewport.get_texture()

## A bone's world position (3D), lifted `lift` units above it.
func bone_world(name: String, lift := 0.0) -> Vector3:
	var id: int = _bone_ids.get(name, skeleton.find_bone(name))
	return skeleton.global_transform * skeleton.get_bone_global_pose(id).origin + Vector3(0.0, lift, 0.0)

## A 3D point in view coordinates.
func to_view(point: Vector3) -> Vector2: return camera.unproject_position(point) / _scale

## Soft-shadow anchors: each body bone dropped onto the seabed, in view coordinates.
func ground_points() -> Array[Vector2]:
	var points: Array[Vector2] = []
	for name in BODY_BONES:
		var p := bone_world(name)
		points.append(to_view(Vector3(p.x, 0.0, p.z)))
	return points

## The body bone a hook lands on: `along` -1 (snout) .. 1 (tail).
static func hook_bone(along: float) -> String:
	return BODY_BONES[clampi(int(round((clampf(along, -1.0, 1.0) + 1.0) * 0.5 * (BODY_BONES.size() - 1))), 0, BODY_BONES.size() - 1)]

## Where the hooked harpoon sits: on the struck bone's back, nudged across.
func hook_point(along: float, across: float) -> Vector2:
	var bone := hook_bone(along)
	return to_view(bone_world(bone, 0.36) + Vector3(clampf(across, -1.0, 1.0) * 0.12, 0.0, 0.0))
