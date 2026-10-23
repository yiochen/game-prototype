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
static var caption_bounds: Dictionary = {}

class NinePatch extends StyleBox:
	var texture: Texture2D
	var region := Rect2()
	var source_margins: Array = []
	var edges: Array = []
	var draw_center := true
	var tint := Color.WHITE
	var minimum_height := 0.0
	var face := Rect2()

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
		minimum_height = float(entry.get("minimum_height", 0.0)) * unit
		var measured: Array = entry.get("face_px", [0, 0, region.size.x, region.size.y])
		face = Rect2(float(measured[0]), float(measured[1]), float(measured[2]), float(measured[3]))

	func face_rect(target: Rect2) -> Rect2:
		var edge_scale := minf(1.0, minf(target.size.x / maxf(float(edges[0]) + float(edges[2]), 0.001), target.size.y / maxf(float(edges[1]) + float(edges[3]), 0.001)))
		var start := Vector2(_mapped(face.position.x, region.size.x, float(source_margins[0]), float(source_margins[2]), target.size.x, float(edges[0]) * edge_scale, float(edges[2]) * edge_scale), _mapped(face.position.y, region.size.y, float(source_margins[1]), float(source_margins[3]), target.size.y, float(edges[1]) * edge_scale, float(edges[3]) * edge_scale))
		var end := Vector2(_mapped(face.end.x, region.size.x, float(source_margins[0]), float(source_margins[2]), target.size.x, float(edges[0]) * edge_scale, float(edges[2]) * edge_scale), _mapped(face.end.y, region.size.y, float(source_margins[1]), float(source_margins[3]), target.size.y, float(edges[1]) * edge_scale, float(edges[3]) * edge_scale))
		return Rect2(target.position + start, end - start)

	static func _mapped(value: float, source_size: float, first: float, last: float, target_size: float, target_first: float, target_last: float) -> float:
		if value <= first and first > 0.0:
			return value * target_first / first
		if value >= source_size - last and last > 0.0:
			return target_size - (source_size - value) * target_last / last
		return target_first + (value - first) * (target_size - target_first - target_last) / maxf(source_size - first - last, 0.001)

	func _get_minimum_size() -> Vector2:
		# Pill art needs its complete source height at the corner scale, not just
		# the sum of its two corner strips. Compressing away the centre span
		# pinches the rounded ends into points even with undistorted corners.
		return Vector2(float(edges[0]) + float(edges[2]), maxf(float(edges[1]) + float(edges[3]), minimum_height))

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

func icon_ink(identity: String) -> Texture2D:
	assert(manifest.icons.has(identity), "Unknown restaurant UI icon: " + identity)
	var key := identity + ":ink"
	if not icons.has(key):
		var entry: Dictionary = manifest.icons[identity]
		var bounds: Array = entry.get("ink_px", [0, 0, entry.region[2], entry.region[3]])
		var result := AtlasTexture.new()
		result.atlas = _texture(entry)
		result.region = Rect2(float(entry.region[0]) + float(bounds[0]), float(entry.region[1]) + float(bounds[1]), float(bounds[2]), float(bounds[3]))
		result.filter_clip = true
		icons[key] = result
	return icons[key]

func face_rect(identity: String, target: Rect2, unit := 1.0, state := "normal") -> Rect2:
	return style(identity, unit, state).face_rect(target)

static func layout_caption(label: Label, target: Rect2, font_size: int) -> void:
	# A font's line box includes ascender/descender reserves that are not ink.
	# Shape through Godot's own text server so ligatures and fallback fonts use
	# the same glyphs as Label, then centre those drawn glyphs on the button face.
	label.add_theme_font_size_override("font_size", font_size)
	var font := label.get_theme_font("font")
	var measured := _caption_metrics(font, label.text, font_size)
	var ink: Rect2 = measured.ink
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.size = Vector2(maxf(float(measured.advance), ink.end.x) + 2, font.get_height(font_size))
	label.position = target.get_center() - Vector2(ink.get_center().x, font.get_ascent(font_size) + ink.get_center().y)

static func caption_ink(font: Font, text: String, font_size: int) -> Rect2:
	return _caption_metrics(font, text, font_size).ink

static func _caption_metrics(font: Font, text: String, font_size: int) -> Dictionary:
	var key := "%s:%d:%s" % [font.get_instance_id(), font_size, text]
	if not caption_bounds.has(key):
		if caption_bounds.size() >= 256:
			caption_bounds.clear()
		var line := TextLine.new()
		line.add_string(text, font, font_size)
		var server := TextServerManager.get_primary_interface()
		var pen := 0.0
		var bounds := Rect2()
		var occupied := false
		for glyph in server.shaped_text_get_glyphs(line.get_rid()):
			for repeat_index in range(int(glyph.repeat)):
				var raster_size := Vector2i(int(glyph.font_size), 0)
				var ink_size := server.font_get_glyph_size(glyph.font_rid, raster_size, int(glyph.index))
				if ink_size.x > 0.0 and ink_size.y > 0.0:
					var offset := server.font_get_glyph_offset(glyph.font_rid, raster_size, int(glyph.index))
					var ink := Rect2(Vector2(pen, 0) + Vector2(glyph.offset) + offset, ink_size)
					bounds = bounds.merge(ink) if occupied else ink
					occupied = true
				pen += float(glyph.advance)
		caption_bounds[key] = {"ink": bounds, "advance": pen}
	return caption_bounds[key]

func content_rect(identity: String, target: Rect2, unit := 1.0, state := "normal") -> Rect2:
	var surface := style(identity, unit, state)
	var start := Vector2(surface.get_margin(SIDE_LEFT), surface.get_margin(SIDE_TOP))
	var end := Vector2(surface.get_margin(SIDE_RIGHT), surface.get_margin(SIDE_BOTTOM))
	return Rect2(target.position + start, (target.size - start - end).max(Vector2.ZERO))

func apply_panel(panel: Panel, identity: String, unit := 1.0, state := "normal") -> void:
	var surface := style(identity, unit, state)
	panel.add_theme_stylebox_override("panel", surface)
	# Panel does not derive its native minimum from its StyleBox as Button
	# does. Apply it explicitly so an undersized layout cannot pinch a pill.
	panel.custom_minimum_size = surface.get_minimum_size()

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
