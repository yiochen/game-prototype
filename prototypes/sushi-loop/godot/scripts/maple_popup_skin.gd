extends RefCounted
## Shared native maple face and close control for recipe and Shop popups.
static func flat(color: Color, radius: float) -> StyleBoxFlat:
	var result := StyleBoxFlat.new()
	result.bg_color = color
	result.set_corner_radius_all(maxi(1,int(radius)))
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]: result.set_content_margin(side,0)
	return result

static func make_face(parent: Control, texture: Texture2D) -> TextureRect:
	var face := TextureRect.new()
	face.texture = texture
	face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	face.stretch_mode = TextureRect.STRETCH_SCALE
	face.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var material := ShaderMaterial.new()
	material.shader = load("res://scripts/maple_face.gdshader")
	face.material = material
	parent.add_child(face)
	return face

static func layout_face(face: TextureRect, dimensions: Vector2, unit: float) -> void:
	face.size = dimensions
	face.material.set_shader_parameter("surface_size",dimensions)
	face.material.set_shader_parameter("corner_radius",32*unit)
	face.material.set_shader_parameter("grain_width",720*unit)

static func close_button(button: Button, unit: float, physical: float) -> void:
	button.size = Vector2(96,96)*unit
	button.custom_minimum_size = Vector2.ONE*44.01/maxf(.001,physical)
	button.add_theme_font_size_override("font_size",maxi(1,int(54*unit)))
	for treatment in ["normal","hover","pressed","disabled"]:
		var style := flat(Color("f5d39e") if treatment == "pressed" else Color("ffe8bc"),48*unit)
		style.shadow_color = Color(.45,.25,.08,.18)
		style.shadow_size = int(5*unit)
		style.shadow_offset = Vector2(0,4)*unit
		button.add_theme_stylebox_override(treatment,style)
	button.add_theme_stylebox_override("focus",StyleBoxEmpty.new())
