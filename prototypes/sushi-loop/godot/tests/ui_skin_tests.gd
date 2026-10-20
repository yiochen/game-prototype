extends SceneTree
## Exercise the actual native StyleBox renderer with an adversarial atlas:
## nine distinct source patches, surrounded by a colour that must never bleed.
## Run --visible for GPU pixel checks; headless still checks native layout.

const RestaurantSkin = preload("res://scripts/ui_skin.gd")
const COLORS := [Color.RED, Color.GREEN, Color.YELLOW, Color.CYAN, Color.BLUE, Color.ORANGE, Color.PURPLE, Color.TEAL, Color.WHITE]
var checks := 0
var failures: Array[String] = []

class Surface extends Control:
	var surface: StyleBox
	var target := Rect2()
	func _draw() -> void:
		draw_style_box(surface, target)

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var texture := _fixture_texture()
	_test_content_and_fit(texture)
	if DisplayServer.get_name() != "headless":
		await _test_rendered_edges(texture)
	else:
		print("Headless: native layout checked; run ui_skin_tests.gd --visible for rendered border regression.")
	if failures.is_empty():
		print("PASS: %s restaurant UI skin checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		quit(1)

func _expect(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)

func _fixture_texture() -> Texture2D:
	var image := Image.create(96, 96, false, Image.FORMAT_RGBA8)
	image.fill(Color.MAGENTA)
	for row in range(3):
		for column in range(3):
			image.fill_rect(Rect2i(12 + column * 24, 12 + row * 24, 24, 24), COLORS[row * 3 + column])
	return ImageTexture.create_from_image(image)

func _entry(draw_center := true) -> Dictionary:
	return {"region": [12, 12, 72, 72], "slice_px": [24, 24, 24, 24], "edge": [18, 18, 18, 18], "content": [16, 16, 16, 16], "draw_center": draw_center}

func _test_content_and_fit(texture: Texture2D) -> void:
	# The same engine Button is resized from a phone control to a wide panel.
	# Insets must follow design scale, and never its changing width/height ratio.
	for unit in [0.5, 1.0, 1.5]:
		var style := RestaurantSkin.NinePatch.new(texture, _entry(), unit)
		var button := Button.new()
		button.add_theme_stylebox_override("normal", style)
		root.add_child(button)
		for target in [Vector2(100, 100), Vector2(420, 70), Vector2(70, 420)]:
			button.size = target * unit
			var actual: StyleBox = button.get_theme_stylebox("normal")
			var equal_insets := true
			for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
				equal_insets = equal_insets and is_equal_approx(actual.get_margin(side), 16.0 * unit)
			_expect(equal_insets, "Native Button preserves four equal 16-unit content insets at scale %s and shape %s" % [unit, target])
			_expect(actual.get_minimum_size().is_equal_approx(Vector2(36, 36) * unit), "Native Button refuses a size that would crush the generated corners")
		button.free()
	for target in [Rect2(5, 8, 80, 80), Rect2(5, 8, 400, 70), Rect2(5, 8, 70, 400)]:
		var fitted := RestaurantSkin.fit_rect(Vector2(80, 120), target)
		_expect(target.encloses(fitted) and fitted.get_center().is_equal_approx(target.get_center()), "An asymmetric icon stays centred and inside its target")
		_expect(is_equal_approx(fitted.size.x / fitted.size.y, 2.0 / 3.0), "Icon fitting preserves its original aspect on square, wide and tall targets")
	_expect(not RestaurantSkin.fit_rect(Vector2.ZERO, Rect2(0, 0, 100, 100)).has_area(), "A missing icon has no invented stretched geometry")

func _test_rendered_edges(texture: Texture2D) -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(800, 700)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var samples := [
		{"rect": Rect2(16, 16, 100, 100), "unit": 0.5, "edge": 9},
		{"rect": Rect2(16, 150, 420, 70), "unit": 1.0, "edge": 18},
		{"rect": Rect2(460, 16, 70, 420), "unit": 1.0, "edge": 18},
		{"rect": Rect2(16, 260, 300, 150), "unit": 1.5, "edge": 27},
	]
	for sample in samples:
		var surface := Surface.new()
		surface.surface = RestaurantSkin.NinePatch.new(texture, _entry(), sample.unit)
		surface.target = sample.rect
		surface.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		viewport.add_child(surface)
	var outline := Surface.new()
	outline.surface = RestaurantSkin.NinePatch.new(texture, _entry(false), 1.0)
	outline.target = Rect2(16, 460, 240, 80)
	outline.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	viewport.add_child(outline)
	for index in range(3):
		await process_frame
	await RenderingServer.frame_post_draw
	var pixels := viewport.get_texture().get_image()
	_expect(pixels != null and pixels.get_size() == viewport.size, "Pixel regression reads the real GPU render target")
	if pixels == null:
		viewport.queue_free()
		return
	for sample in samples:
		var rect: Rect2 = sample.rect
		var edge: int = sample.edge
		var x := int(rect.position.x)
		var y := int(rect.position.y)
		var width := int(rect.size.x)
		var height := int(rect.size.y)
		var corners := true
		# Check the full corner area, including each last row/column. A stretched
		# source or a border derived from width would fail on the tall/wide cases.
		for offset in range(edge):
			corners = corners and _color(pixels, x + offset, y + edge - 1, Color.RED)
			corners = corners and _color(pixels, x + edge - 1, y + offset, Color.RED)
			corners = corners and _color(pixels, x + width - 1 - offset, y + edge - 1, Color.YELLOW)
			corners = corners and _color(pixels, x + width - edge, y + offset, Color.YELLOW)
			corners = corners and _color(pixels, x + offset, y + height - edge, Color.PURPLE)
			corners = corners and _color(pixels, x + edge - 1, y + height - 1 - offset, Color.PURPLE)
			corners = corners and _color(pixels, x + width - 1 - offset, y + height - edge, Color.WHITE)
			corners = corners and _color(pixels, x + width - edge, y + height - 1 - offset, Color.WHITE)
		_expect(corners, "Rendered %s × %s control retains four square %s px corners" % [width, height, edge])
		var boundaries := _color(pixels, x + edge, y + edge - 1, Color.GREEN) and _color(pixels, x + width - edge - 1, y + edge - 1, Color.GREEN)
		boundaries = boundaries and _color(pixels, x + edge - 1, y + edge, Color.CYAN) and _color(pixels, x + width - edge, y + edge, Color.ORANGE)
		boundaries = boundaries and _color(pixels, x + edge, y + height - edge, Color.TEAL) and _color(pixels, x + width - edge - 1, y + height - edge, Color.TEAL)
		_expect(boundaries, "All four border transitions stay at the declared design scale, independent of aspect")
		var centre := _color(pixels, x + width / 2, y + height / 2, Color.BLUE)
		var inside := _color(pixels, x + edge, y + edge, Color.BLUE) and _color(pixels, x + width - edge - 1, y + height - edge - 1, Color.BLUE)
		_expect(centre and inside, "Only the centre expands; neighboring atlas pixels do not enter its region")
	_expect(pixels.get_pixel(100, 500).a < 0.01 and _color(pixels, 20, 464, Color.RED), "Generated focus framing leaves the control centre transparent")
	viewport.queue_free()

func _color(image: Image, x: int, y: int, expected: Color) -> bool:
	var actual := image.get_pixel(x, y)
	return absf(actual.r - expected.r) < 0.03 and absf(actual.g - expected.g) < 0.03 and absf(actual.b - expected.b) < 0.03 and actual.a > 0.98
