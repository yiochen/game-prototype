extends SceneTree
## Bakes the approved #61 cash and tip-jar art into the `assets/tips/` ArtBook
## pack and the UI cash icon. Sources are the approved review files in
## design/cash-preview/assets (2D SVG cash, Blender tip-jar renders).
##   godot --headless --path prototypes/sushi-loop/godot --script res://tools/bake_tip_art.gd
## Interactive art gets the approved cyan outline with a soft glow, baked here
## so the world renderer draws ordinary sprites. The outline sits only outside
## the solid silhouette, so it never shows through the jar's glass.

const SOURCE := "../design/cash-preview/assets/"
const OUT := "res://assets/tips/"
const OUTLINE := Color("19e3ff")
## In 256 px-per-cell source pixels: the approved 2.5 px ring and 3 px glow on a
## 61.6 px phone cell.
const RING := 10.0
const GLOW := 14.0
const SOLID_ALPHA := 0.05

func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT + "sprites"))
	var objects := {}
	# Cash piles: SVG 256x192 drawn 1.5 cells wide, floating just above the tile centre.
	for tier in [1, 2, 3]:
		var art := svg("cash-%d.svg" % tier, 1.5)
		var frame := Image.create_empty(384, 384, false, Image.FORMAT_RGBA8)
		frame.blend_rect(art, Rect2i(Vector2i.ZERO, art.get_size()), Vector2i(0, 48))
		save(outlined(frame), "cash-%d.png" % tier)
		objects["cash-%d" % tier] = record("cash-%d" % tier, {"static": "cash-%d.png" % tier}, [192, 192], [96, 106])
	# Tip jar: one south view, five fill states. The empty jar has no outline:
	# there is nothing to collect.
	var jar_clips := {}
	for state in ["empty", "quarter", "half", "most", "full"]:
		var image := Image.load_from_file(ProjectSettings.globalize_path("res://") + SOURCE + "jar-%s.png" % state)
		image.convert(Image.FORMAT_RGBA8)
		var clip: String = "static" if state == "empty" else state
		save(image if state == "empty" else outlined(image), "tip-jar-%s.png" % state)
		jar_clips[clip] = "tip-jar-%s.png" % state
	objects["tip-jar"] = record("tip-jar", jar_clips, [192, 384], [96, 288])
	# Feedback icons drawn above guests: the sale pop, a tea request and a secured tip.
	for entry in [["cash-pop", "cash-pop.svg", 2.0, [160, 120], [80, 104]], ["tea-bubble", "tea-bubble.svg", 1.5, [96, 96], [48, 96]], ["tip-check", "tip-check.svg", 1.5, [96, 96], [48, 96]]]:
		save(svg(entry[1], entry[2]), entry[0] + ".png")
		objects[entry[0]] = record(entry[0], {"static": entry[0] + ".png"}, entry[3], entry[4])
	var manifest := {"version": 1, "cellSize": 128, "source": "design/cash-preview (approved 2026-11-07)", "policy": "Baked by tools/bake_tip_art.gd; do not edit by hand.", "objects": objects}
	var file := FileAccess.open(OUT + "manifest.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest, "\t"))
	file.close()
	# The HUD and price icon.
	svg("cash-icon.svg", 2.0).save_png(ProjectSettings.globalize_path("res://assets/ui/cash.png"))
	print("Baked tip art: ", objects.keys())
	quit(0)

func svg(name: String, scale: float) -> Image:
	var image := Image.new()
	var error := image.load_svg_from_string(FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://") + SOURCE + name), scale)
	assert(error == OK, "Could not rasterize " + name)
	image.convert(Image.FORMAT_RGBA8)
	return image

func save(image: Image, name: String) -> void:
	image.save_png(ProjectSettings.globalize_path(OUT + "sprites/" + name))

func record(identity: String, clips: Dictionary, frame_size: Array, root: Array) -> Dictionary:
	var result := {"id": identity, "footprint": [1, 1], "clips": {}}
	for clip in clips:
		var image := Image.load_from_file(ProjectSettings.globalize_path(OUT + "sprites/" + clips[clip]))
		result.clips[clip] = {"frames": 1, "fps": 1, "loop": false, "directions": {"S": {
			"image": "sprites/" + clips[clip], "frames": 1, "rects": [[0, 0, image.get_width(), image.get_height()]],
			"frameSize": frame_size, "root": root, "sourceScale": 2,
			"sha256": FileAccess.get_sha256(OUT + "sprites/" + clips[clip])}}}
	return result

## The approved outline: a solid ring outside the silhouette plus a fading glow.
func outlined(source: Image) -> Image:
	var width := source.get_width()
	var height := source.get_height()
	var far := 1.0e9
	var distance := PackedFloat32Array()
	distance.resize(width * height)
	for y in height:
		for x in width:
			distance[y * width + x] = 0.0 if source.get_pixel(x, y).a > SOLID_ALPHA else far
	# Two-pass chamfer distance to the nearest solid pixel.
	var diagonal := sqrt(2.0)
	for y in height:
		for x in width:
			var i := y * width + x
			var best := distance[i]
			if x > 0: best = minf(best, distance[i - 1] + 1.0)
			if y > 0:
				best = minf(best, distance[i - width] + 1.0)
				if x > 0: best = minf(best, distance[i - width - 1] + diagonal)
				if x < width - 1: best = minf(best, distance[i - width + 1] + diagonal)
			distance[i] = best
	for y in range(height - 1, -1, -1):
		for x in range(width - 1, -1, -1):
			var i := y * width + x
			var best := distance[i]
			if x < width - 1: best = minf(best, distance[i + 1] + 1.0)
			if y < height - 1:
				best = minf(best, distance[i + width] + 1.0)
				if x < width - 1: best = minf(best, distance[i + width + 1] + diagonal)
				if x > 0: best = minf(best, distance[i + width - 1] + diagonal)
			distance[i] = best
	var result := Image.create_empty(width, height, false, Image.FORMAT_RGBA8)
	for y in height:
		for x in width:
			var d := distance[y * width + x]
			var alpha := 0.0
			if d > 0.0 and d <= RING + GLOW:
				var ring := clampf(RING + 0.5 - d, 0.0, 1.0)
				var glow := 0.9 * pow(clampf(1.0 - (d - RING) / GLOW, 0.0, 1.0), 2.0)
				alpha = maxf(ring, glow)
			var outline := Color(OUTLINE, alpha)
			var art := source.get_pixel(x, y)
			# Art over outline (premultiplied "over").
			var a := art.a + outline.a * (1.0 - art.a)
			var color := (Color(art.r, art.g, art.b) * art.a + Color(outline.r, outline.g, outline.b) * outline.a * (1.0 - art.a)) / maxf(a, 0.0001)
			result.set_pixel(x, y, Color(color.r, color.g, color.b, a))
	return result
