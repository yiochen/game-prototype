extends SceneTree
## Isolated Compatibility-renderer proof; no game scripts, UI or saves loaded.
var lights: Array[PointLight2D] = []
var destination := ""
var records: Array = []
var probes := {}

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    destination = OS.get_environment("BACKDROP_PROOF_OUTPUT")
    if destination.is_empty():
        push_error("Missing isolated proof output")
        quit(1)
        return
    root.size = Vector2i(1120, 480)
    var canvas := Node2D.new()
    root.add_child(canvas)
    var ambient := CanvasModulate.new()
    ambient.color = Color(1, 1, 1, 1)
    canvas.add_child(ambient)
    var atlas := AtlasTexture.new()
    atlas.atlas = load("res://assembled.png")
    atlas.region = Rect2(96, 96, 2688, 1152)
    var wall := Sprite2D.new()
    wall.centered = false
    wall.texture = atlas
    wall.scale = Vector2.ONE * (1120.0 / 2688.0)
    wall.light_mask = 1
    canvas.add_child(wall)
    var gradient := Gradient.new()
    gradient.offsets = PackedFloat32Array([0, .20, .65, 1])
    gradient.colors = PackedColorArray([Color.WHITE, Color(.78,.78,.78,1), Color(.16,.16,.16,1), Color(0,0,0,1)])
    var texture := GradientTexture2D.new()
    texture.width = 512
    texture.height = 512
    texture.fill = GradientTexture2D.FILL_RADIAL
    texture.fill_from = Vector2(.5,.5)
    texture.fill_to = Vector2(.5,0)
    texture.gradient = gradient
    var calibration: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://camera.json"))
    for emitter in calibration.lanternLights:
        var light := PointLight2D.new()
        light.name = str(emitter.id) + "_lantern"
        light.position = Vector2(float(emitter.positionTiles[0]), float(emitter.positionTiles[1])) * 160
        light.texture = texture
        light.texture_scale = .95
        light.color = Color(1,.72,.32,1)
        light.height = 120
        light.shadow_enabled = false
        light.range_item_cull_mask = 1
        canvas.add_child(light)
        lights.append(light)
    probes = {"left": Vector2i(lights[0].position + Vector2(-120,40)), "right": Vector2i(lights[1].position + Vector2(120,40))}
    for state in [["ambient", 0.0, 0.0], ["lanterns", .12, .12], ["left-dim", .02, .12]]:
        for i in range(2):
            lights[i].enabled = float(state[i+1]) > 0
            lights[i].energy = float(state[i+1])
        await process_frame
        await process_frame
        await RenderingServer.frame_post_draw
        var pixels := root.get_texture().get_image()
        pixels.save_png(destination.path_join(str(state[0]) + ".png"))
        var colors := {}
        for name in probes:
            var color := pixels.get_pixelv(probes[name])
            colors[name] = [color.r,color.g,color.b]
        records.append({"id":state[0],"energies":[state[1],state[2]],"probeColors":colors,"pixels":[pixels.get_width(),pixels.get_height()]})
    var brightened: bool = float(records[1].probeColors.left[0]) > float(records[0].probeColors.left[0]) + .005
    var independent: bool = float(records[2].probeColors.left[0]) < float(records[1].probeColors.left[0]) - .005
    var right_stable: bool = absf(float(records[2].probeColors.right[0]) - float(records[1].probeColors.right[0])) < .005
    var file := FileAccess.open(destination.path_join("lighting-check.json"), FileAccess.WRITE)
    file.store_string(JSON.stringify({"renderer":RenderingServer.get_current_rendering_method(),"method":"PointLight2D + Sprite2D + CanvasModulate; no normal map, bloom or post-process", "spriteSourceSha256":FileAccess.get_sha256("res://assembled.png"),"ambientUniform":true,"probePositions":{"left":[probes.left.x,probes.left.y],"right":[probes.right.x,probes.right.y]},"states":records,"checks":{"lightBrightensSprite":brightened,"leftDimmingIndependent":independent,"rightUnaffected":right_stable}},"\t"))
    file.close()
    if not brightened or not independent or not right_stable:
        push_error("Native 2D light proof failed")
        quit(1)
    else:
        print("PASS: Sprite receives independently adjustable lantern light in the Compatibility renderer")
        quit(0)
