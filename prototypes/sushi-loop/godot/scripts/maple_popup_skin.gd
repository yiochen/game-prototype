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

## The cream catalog's inner shadow (recipe-maple.css `.wr-catalog`: inset 0 2px 4px #80542e24).
static func inner_shadow(parent: Control) -> ColorRect:
	var shade := ColorRect.new()
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var material := ShaderMaterial.new()
	material.shader = load("res://scripts/inner_shadow.gdshader")
	material.set_shader_parameter("shadow_color",Color("80542e24"))
	shade.material = material
	parent.add_child(shade)
	return shade

static func layout_inner_shadow(shade: ColorRect, bounds: Rect2, radius: float, unit: float) -> void:
	shade.position = bounds.position
	shade.size = bounds.size
	shade.material.set_shader_parameter("rect_size",bounds.size)
	shade.material.set_shader_parameter("radius",radius)
	shade.material.set_shader_parameter("offset",Vector2(0,2)*unit)
	shade.material.set_shader_parameter("blur",4*unit)

## The drop shadow under every maple popup card (the face is a make_face child).
static func card_shadow(radius: float, unit: float) -> StyleBoxFlat:
	var shadow := flat(Color.TRANSPARENT,radius)
	shadow.shadow_color = Color(.35,.18,.05,.24)
	shadow.shadow_size = int(7*unit)
	shadow.shadow_offset = Vector2(0,5)*unit
	return shadow

## The shared keyboard focus ring (GameButton.FOCUS), drawn just outside a control.
static func focus_ring(radius: float, unit: float) -> StyleBoxFlat:
	var ring := flat(Color.TRANSPARENT,radius+3*unit)
	ring.border_color = Color("32636b")
	ring.set_border_width_all(maxi(1,int(2*unit)))
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]: ring.set_expand_margin(side,3*unit)
	return ring

## Round cream icon button (close X, Shop bag): `diameter` in design units.
static func round_button(button: Button, unit: float, physical: float, diameter := 96.0) -> void:
	button.size = Vector2.ONE*diameter*unit
	button.custom_minimum_size = Vector2.ONE*44.01/maxf(.001,physical)
	for treatment in ["normal","hover","pressed","disabled"]:
		var style := flat(Color("f5d39e") if treatment == "pressed" else Color("ffe8bc"),diameter*.5*unit)
		style.shadow_color = Color(.45,.25,.08,.18)
		style.shadow_size = int(5*unit)
		style.shadow_offset = Vector2(0,4)*unit
		button.add_theme_stylebox_override(treatment,style)
	button.add_theme_stylebox_override("focus",focus_ring(diameter*.5*unit,unit))
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_hover_pressed_color"]: button.add_theme_color_override(key,Color("592c10"))

static func close_button(button: Button, unit: float, physical: float) -> void:
	round_button(button,unit,physical)
	button.custom_minimum_size = Vector2.ONE*44.01/maxf(.001,physical)
	button.add_theme_font_size_override("font_size",maxi(1,int(54*unit)))
