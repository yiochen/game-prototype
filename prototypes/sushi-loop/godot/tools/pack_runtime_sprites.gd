extends SceneTree
## Android staging only: rewrite a staged copy's sprite atlases for phones.
## Each authored frame is downscaled to SCALE, trimmed to its visible pixels
## and shelf-packed. Approved manifests stay byte-identical; ArtBook reads the
## new regions and trims from runtime_pack.json beside each manifest.
##   godot --headless --path <staged project> --script res://tools/pack_runtime_sprites.gd

## 256 source pixels per cell become 224, about 1:1 on a Pixel 10 Pro XL
## (1344 px wide, ~218 px per cell). Authored rects are multiples of 8 px.
const SCALE := 0.875
## Transparent gutter keeps bilinear sampling from bleeding between frames.
const GUTTER := 2
const MAX_WIDTH := 4096
const DIRECTORIES := ["res://assets/catalog/", "res://assets/recipe-variants/", "res://assets/chef-variants/", "res://assets/feedback-variants/", "res://assets/expansion/"]
## EntranceCurtain samples this atlas by absolute authored coordinates.
const UNPACKED := ["backdrop-entrance"]

func _init() -> void:
	var before := 0
	var after := 0
	for directory in DIRECTORIES:
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory + "manifest.json"))
		var frames := {}
		var keep := {}
		for identity in manifest.get("objects", {}):
			var clips: Dictionary = manifest.objects[identity].get("clips", {})
			for clip in clips:
				for entry in clips[clip].directions.values():
					var image := str(entry.image)
					if identity in UNPACKED: keep[image] = true
					if not frames.has(image): frames[image] = {}
					for rect in entry.rects:
						frames[image]["%d,%d,%d,%d" % [rect[0], rect[1], rect[2], rect[3]]] = rect
		var images := {}
		for image in frames:
			if keep.has(image): continue
			var path := ProjectSettings.globalize_path(directory + image)
			var source := Image.load_from_file(path)
			if source == null:
				push_error("Cannot read runtime atlas " + path)
				quit(1)
				return
			before += source.get_width() * source.get_height()
			source.convert(Image.FORMAT_RGBA8)
			var packed := _pack(source, frames[image])
			packed.atlas.save_png(path)
			after += packed.atlas.get_width() * packed.atlas.get_height()
			images[image] = {"size": [packed.atlas.get_width(), packed.atlas.get_height()], "frames": packed.frames}
		var pack_file := FileAccess.open(directory + "runtime_pack.json", FileAccess.WRITE)
		pack_file.store_string(JSON.stringify({"scale": SCALE, "images": images}))
		pack_file.close()
	print("Packed runtime sprites: %.1f -> %.1f Mpx" % [before / 1e6, after / 1e6])
	quit(0)

func _pack(source: Image, rects: Dictionary) -> Dictionary:
	var pieces: Array = []
	var by_content := {}
	for key in rects:
		var r: Array = rects[key]
		var frame := source.get_region(Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3])))
		var size := Vector2i(roundi(r[2] * SCALE), roundi(r[3] * SCALE))
		# Spread edge colour into transparent texels so resampling has no dark fringe.
		frame.fix_alpha_edges()
		frame.resize(size.x, size.y, Image.INTERPOLATE_LANCZOS)
		var used := frame.get_used_rect()
		used = Rect2i(0, 0, 1, 1) if not used.has_area() else used.grow(1).intersection(Rect2i(Vector2i.ZERO, size))
		var pixels := frame.get_region(used)
		# Held poses repeat identical frames; store each distinct crop once.
		var content := "%s:%d" % [used, hash(pixels.get_data())]
		var piece: Dictionary = by_content.get(content, {})
		if piece.is_empty():
			piece = {"pixels": pixels, "keys": []}
			by_content[content] = piece
			pieces.append(piece)
		piece.keys.append([key, used, size])
	pieces.sort_custom(func(a, b): return a.pixels.get_height() > b.pixels.get_height())
	var area := 0
	var widest := 0
	for piece in pieces:
		area += (piece.pixels.get_width() + GUTTER) * (piece.pixels.get_height() + GUTTER)
		widest = maxi(widest, piece.pixels.get_width() + GUTTER)
	var width := clampi(int(ceil(sqrt(area * 1.15))), widest, maxi(widest, MAX_WIDTH))
	var cursor := Vector2i.ZERO
	var row_height := 0
	for piece in pieces:
		var piece_size: Vector2i = piece.pixels.get_size()
		if cursor.x + piece_size.x > width:
			cursor = Vector2i(0, cursor.y + row_height + GUTTER)
			row_height = 0
		piece.position = cursor
		cursor.x += piece_size.x + GUTTER
		row_height = maxi(row_height, piece_size.y)
	var atlas := Image.create_empty(width, cursor.y + row_height, false, Image.FORMAT_RGBA8)
	var records := {}
	for piece in pieces:
		atlas.blit_rect(piece.pixels, Rect2i(Vector2i.ZERO, piece.pixels.get_size()), piece.position)
		for record in piece.keys:
			var used: Rect2i = record[1]
			var size: Vector2i = record[2]
			records[record[0]] = [piece.position.x, piece.position.y, used.size.x, used.size.y, used.position.x, used.position.y, used.size.x, used.size.y, size.x, size.y]
	return {"atlas": atlas, "frames": records}
