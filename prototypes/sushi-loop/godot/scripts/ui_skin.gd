extends RefCounted
## One generated restaurant UI family with independent source and logical slices.
## Source pixels never become layout pixels: only the centre and edge lengths
## adapt to a control's aspect ratio. Corner shapes scale uniformly with unit.

const MANIFEST := "res://assets/ui/editor/manifest.json"
const SIDES := [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]

var manifest: Dictionary = {}
var directory := ""
var textures: Dictionary = {}
var styles: Dictionary = {}
var icons: Dictionary = {}

class NinePatch extends StyleBox:
	var texture: Texture2D
	var region := Rect2()
	var source_margins: Array = []
	var edges: Array = []
	var draw_center := true
	var tint := Color.WHITE

	func _init(source_texture: Texture2D, entry: Dictionary, unit: float) -> void:
		texture = source_texture
		var source: Array = entry.region
		region = Rect2(float(source[0]), float(source[1]), float(source[2]), float(source[3]))
		source_margins = entry.slice_px.duplicate()
		for value in entry.edge:
			edges.append(float(value) * unit)
		for index in range(4):
			set_content_margin(SIDES[index], float(entry.content[index]) * unit)
		draw_center = bool(entry.get("draw_center", true))
		tint = Color(str(entry.get("tint", "ffffffff")))

	func _get_minimum_size() -> Vector2:
		return Vector2(float(edges[0]) + float(edges[2]), float(edges[1]) + float(edges[3]))

	func _draw(canvas: RID, rect: Rect2) -> void:
		if texture == null or not rect.has_area():
			return
		# A style's minimum size normally prevents this case. For direct drawing
		# into a smaller rectangle, scale all four corners by one common factor.
		var edge_scale := minf(1.0, minf(rect.size.x / maxf(float(edges[0]) + float(edges[2]), 0.001), rect.size.y / maxf(float(edges[1]) + float(edges[3]), 0.001)))
		var dx := [rect.position.x, rect.position.x + float(edges[0]) * edge_scale, rect.end.x - float(edges[2]) * edge_scale, rect.end.x]
		var dy := [rect.position.y, rect.position.y + float(edges[1]) * edge_scale, rect.end.y - float(edges[3]) * edge_scale, rect.end.y]
		var sx := [region.position.x, region.position.x + float(source_margins[0]), region.end.x - float(source_margins[2]), region.end.x]
		var sy := [region.position.y, region.position.y + float(source_margins[1]), region.end.y - float(source_margins[3]), region.end.y]
		for row in range(3):
			for column in range(3):
				if row == 1 and column == 1 and not draw_center:
					continue
				var destination := Rect2(float(dx[column]), float(dy[row]), float(dx[column + 1]) - float(dx[column]), float(dy[row + 1]) - float(dy[row]))
				var source := Rect2(float(sx[column]), float(sy[row]), float(sx[column + 1]) - float(sx[column]), float(sy[row + 1]) - float(sy[row]))
				if destination.has_area() and source.has_area():
					texture.draw_rect_region(canvas, destination, source, tint, false, true)

func _init(manifest_path: String = MANIFEST) -> void:
	directory = manifest_path.get_base_dir()
	var data = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	assert(data is Dictionary and data.has("styles") and data.has("icons"), "Restaurant UI skin manifest is missing styles or icons")
	manifest = data

func style(identity: String, unit := 1.0, state := "normal") -> StyleBox:
	assert(unit > 0.0 and manifest.styles.has(identity), "Unknown restaurant UI style: " + identity)
	var key := "%s:%0.6f:%s" % [identity, unit, state]
	if not styles.has(key):
		var entry: Dictionary = manifest.styles[identity].duplicate(true)
		var treatment = entry.get("states", {}).get(state)
		if treatment is String:
			assert(manifest.styles.has(treatment), "Unknown restaurant UI state style: " + treatment)
			entry = manifest.styles[treatment].duplicate(true)
		elif treatment is Dictionary:
			entry.merge(treatment, true)
		styles[key] = NinePatch.new(_texture(entry), entry, unit)
	return styles[key]

func icon(identity: String) -> Texture2D:
	assert(manifest.icons.has(identity), "Unknown restaurant UI icon: " + identity)
	if not icons.has(identity):
		var entry: Dictionary = manifest.icons[identity]
		var source: Array = entry.region
		var result := AtlasTexture.new()
		result.atlas = _texture(entry)
		result.region = Rect2(float(source[0]), float(source[1]), float(source[2]), float(source[3]))
		result.filter_clip = true
		icons[identity] = result
	return icons[identity]

func content_rect(identity: String, target: Rect2, unit := 1.0, state := "normal") -> Rect2:
	var surface := style(identity, unit, state)
	var start := Vector2(surface.get_margin(SIDE_LEFT), surface.get_margin(SIDE_TOP))
	var end := Vector2(surface.get_margin(SIDE_RIGHT), surface.get_margin(SIDE_BOTTOM))
	return Rect2(target.position + start, (target.size - start - end).max(Vector2.ZERO))

static func fit_rect(native_size: Vector2, target: Rect2) -> Rect2:
	if native_size.x <= 0.0 or native_size.y <= 0.0 or not target.has_area():
		return Rect2(target.get_center(), Vector2.ZERO)
	var fitted := native_size * minf(target.size.x / native_size.x, target.size.y / native_size.y)
	return Rect2(target.get_center() - fitted * 0.5, fitted)

func _texture(entry: Dictionary) -> Texture2D:
	var path: String = str(entry.get("image", manifest.get("atlas", "")))
	assert(not path.is_empty(), "Restaurant UI entry is missing its generated image")
	if not path.begins_with("res://") and not path.begins_with("user://") and not path.is_absolute_path():
		path = directory.path_join(path)
	if not textures.has(path):
		textures[path] = load(path)
	assert(textures[path] is Texture2D, "Restaurant UI texture could not load: " + path)
	return textures[path]
