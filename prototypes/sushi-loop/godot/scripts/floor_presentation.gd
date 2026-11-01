extends Control
## Same native scene instructions, edge controls and brush exit in play/gallery.
signal brush_exited
signal pan_requested(direction: Vector2)
const Typography = preload("res://scripts/typography.gd")
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
var instruction: Label
var exit_button: Button
var carets: Dictionary = {}
var state: Dictionary = {}
var area := Rect2()
var palette_rect := Rect2()
var top := 0.0
var bottom := 0.0
var touching := false
var held := Vector2.ZERO
var held_pointer := -1
var limits := Vector2.ZERO
class Chevron extends Control:
	var angle := 0.0
	func _draw() -> void:
		draw_set_transform(size*.5,angle,Vector2.ONE*size.x/44.0)
		var points := PackedVector2Array([Vector2(5,-8),Vector2(-3,0),Vector2(5,8)])
		draw_polyline(points,Color("765033"),4.5,true)
		draw_polyline(points,Color("fff7dc"),3,true)
func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	instruction = Label.new();instruction.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var instruction_font:=Typography.body();instruction_font.variation_opentype={TextServerManager.get_primary_interface().name_to_tag("wght"):900}
	instruction.add_theme_font_override("font",instruction_font);instruction.add_theme_color_override("font_color",Color("fffbea"))
	instruction.add_theme_color_override("font_shadow_color",Color("57361f"));instruction.add_theme_constant_override("shadow_offset_y",2);instruction.add_theme_constant_override("shadow_outline_size",5)
	instruction.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;instruction.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	instruction.accessibility_live=AccessibilityServer.LIVE_POLITE
	add_child(instruction)
	exit_button=Button.new();exit_button.text="×";exit_button.accessibility_name="Exit floor brush";exit_button.add_theme_font_override("font",Typography.body());add_child(exit_button)
	for treatment in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:exit_button.add_theme_color_override(treatment,Color("61381e"))
	exit_button.pressed.connect(func(): brush_exited.emit())
	for dir in ["left","right","up","down"]:
		var button := Button.new();button.accessibility_name="Pan scene "+dir
		for treatment in ["normal","hover","pressed","disabled"]:button.add_theme_stylebox_override(treatment,StyleBoxEmpty.new())
		var focus:=StyleBoxFlat.new();focus.bg_color=Color.TRANSPARENT;focus.border_color=Color("244d72");focus.set_border_width_all(2);focus.set_corner_radius_all(8);button.add_theme_stylebox_override("focus",focus)
		add_child(button)
		var arrow:=Chevron.new();arrow.mouse_filter=Control.MOUSE_FILTER_IGNORE;arrow.angle={"left":0.0,"right":PI,"up":PI*.5,"down":-PI*.5}[dir];button.add_child(arrow)
		var vector:Vector2={"left":Vector2.LEFT,"right":Vector2.RIGHT,"up":Vector2.UP,"down":Vector2.DOWN}[dir]
		button.gui_input.connect(func(event):
			if button.disabled:return
			if event is InputEventScreenTouch and event.pressed:
				held=vector;held_pointer=event.index;pan_requested.emit(vector*.5);button.accept_event()
			elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
				held=vector if event.pressed else Vector2.ZERO
				if event.pressed:pan_requested.emit(vector*.5)
				button.accept_event()
			elif event is InputEventKey and event.pressed and event.keycode in [KEY_ENTER,KEY_KP_ENTER,KEY_SPACE]:pan_requested.emit(vector);button.accept_event())
		carets[dir]=button
	hide()
func refresh(value: Dictionary, portrait: Rect2, palette: Rect2, occlusion: float, max_camera: Vector2, blocked: bool) -> void:
	state=value;area=portrait;palette_rect=palette;limits=max_camera
	visible=not blocked and state.get("mode")=="edit" and state.get("editor",{}).get("layer")=="floor"
	if not visible: cancel();return
	var unit:=area.size.x/720.0
	var physical:=maxf(.001,get_viewport_transform().get_scale().x)
	var edge:=maxf(80*unit,44.01/physical)
	top=area.position.y+145*unit;bottom=occlusion
	instruction.text="paint the floor" if not str(state.editor.get("floor_brush","")).is_empty() else "select a tile pattern" if state.editor.tray_open else ""
	instruction.add_theme_font_size_override("font_size",maxi(1,int(36*unit)))
	instruction.position=Vector2(area.position.x+edge,(top+bottom)*.5-32*unit);instruction.size=Vector2(area.size.x-edge*2,64*unit)
	instruction.visible=not touching and instruction.text!=""
	exit_button.visible=not str(state.editor.get("floor_brush","")).is_empty()
	PopupSkin.close_button(exit_button,unit,physical);exit_button.position=Vector2(area.end.x-exit_button.size.x-22*unit,bottom-exit_button.size.y-24*unit)
	for dir in carets:
		var button:Button=carets[dir];button.size=Vector2.ONE*edge
		var center:=Vector2(area.position.x+edge*.5,(top+bottom)*.5)
		if dir=="right":center.x=area.end.x-edge*.5
		elif dir=="up":center=Vector2(area.get_center().x,top+edge*.5)
		elif dir=="down":center=Vector2(area.get_center().x,bottom-edge*.5-8*unit)
		button.position=center-button.size*.5
		var arrow:Control=button.get_child(0);arrow.size=button.size;arrow.queue_redraw()
		button.disabled={"left":float(state.camera.x)<=.001,"right":float(state.camera.x)>=limits.x-.001,"up":float(state.camera.y)<=.001,"down":float(state.camera.y)>=limits.y-.001}[dir]
		button.modulate.a=.22 if button.disabled else 1.0
func _input(event: InputEvent) -> void:
	if not visible:return
	if event is InputEventScreenTouch or (event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT):
		if event.pressed:
			var at:Vector2=get_global_transform_with_canvas().affine_inverse()*event.position
			if not palette_rect.has_point(at):touching=true
		else:touching=false;held=Vector2.ZERO;held_pointer=-1
		instruction.visible=not touching and instruction.text!=""
	elif event is InputEventScreenDrag and event.index==held_pointer:get_viewport().set_input_as_handled()
func _process(delta:float) -> void:
	if visible and held!=Vector2.ZERO:pan_requested.emit(held*minf(delta,.05)*3.0)
func cancel() -> void:
	touching=false;held=Vector2.ZERO;held_pointer=-1
	if is_instance_valid(exit_button) and exit_button.is_pressed():
		var was_disabled:=exit_button.disabled
		exit_button.disabled=true;exit_button.disabled=was_disabled
func _notification(what:int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:cancel()

func blocked_rects() -> Array[Rect2]:
	var result:Array[Rect2]=[]
	if not visible:return result
	for button in carets.values()+[exit_button]:
		if button.is_visible_in_tree():result.append(button.get_global_rect())
	return result
