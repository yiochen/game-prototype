extends Control
## Same approved #19 maple confirmation in gameplay and --clearance-gallery.
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const Art = preload("res://scripts/art_book.gd")
const Typography = preload("res://scripts/typography.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
signal confirmed(identity: String)
signal reveal_confirmed
signal unlock_go_requested
signal closed
var art = Art.new()
var wood = Wood.new()
var panel: Panel
var face: TextureRect
var title: Label
var well: Panel
var preview: Preview
var cancel: Button
var clear_button: Button
var clear_caption: Label
var price_label: Label
var price_coin: TextureRect
var samples: HBoxContainer
var patch: Dictionary = {}
var state: Dictionary = {}
var area := Rect2()
var gallery := false
var sample := "normal"
var busy := false
var destination := ""
var reveal_confirmation := false
var unlock_popup := false
var unlock_art: TextureRect
var close_button: Button
var focused_before: Control

class Preview extends Control:
	var art_book
	var entry: Dictionary = {}
	func _draw() -> void:
		if entry.is_empty(): return
		var clip := "static" if entry.get("landmark",false) else "clearance-static"
		var frame: Dictionary = art_book.frame_data(str(entry.art_id),clip,str(entry.get("facing","S")))
		if frame.is_empty(): return
		var direction: Dictionary = art_book.direction_data(str(entry.art_id),clip,str(entry.get("facing","S")))
		var visible: Array = direction.get("visibleBounds",[0,0,frame.region.size.x,frame.region.size.y])
		var region := Rect2(float(visible[0]),float(visible[1]),float(visible[2]),float(visible[3]))
		var scale_value := minf(size.x/region.size.x,size.y/region.size.y)
		draw_texture_rect_region(frame.texture,Rect2((size-region.size*scale_value)*.5,region.size*scale_value),region)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	art.reload()
	var scrim := ColorRect.new();scrim.color = Color(.10,.14,.21,.19);scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(scrim)
	panel = Panel.new();panel.mouse_filter = Control.MOUSE_FILTER_STOP;panel.accessibility_name = "Garbage clearance";add_child(panel)
	face = PopupSkin.make_face(panel,wood.texture("wood-grain"))
	title = Label.new();title.text = "Clear this patch?";title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var heading := Typography.body();heading.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):950}
	title.add_theme_font_override("font",heading);title.add_theme_color_override("font_color",Color("592c10"));title.mouse_filter = Control.MOUSE_FILTER_IGNORE;panel.add_child(title)
	well = Panel.new();well.mouse_filter = Control.MOUSE_FILTER_IGNORE;panel.add_child(well)
	preview = Preview.new();preview.art_book = art;preview.mouse_filter = Control.MOUSE_FILTER_IGNORE;well.add_child(preview)
	cancel = _button("Cancel",panel);clear_button = _button("",panel)
	clear_caption = Label.new();clear_caption.text = "Clear";clear_caption.mouse_filter = Control.MOUSE_FILTER_IGNORE;clear_button.add_child(clear_caption)
	price_label = Label.new();price_label.mouse_filter = Control.MOUSE_FILTER_IGNORE;clear_button.add_child(price_label)
	price_coin = TextureRect.new();price_coin.texture = UISkin.new().icon_ink("coin");price_coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE;price_coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED;price_coin.mouse_filter = Control.MOUSE_FILTER_IGNORE;clear_button.add_child(price_coin)
	unlock_art = TextureRect.new();unlock_art.texture = load("res://assets/ui/exhibition/underwater.webp")
	unlock_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE;unlock_art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED;unlock_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
	unlock_art.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	unlock_art.accessibility_name = "A yellow submarine exploring turquoise water among coral, fish and ancient underwater ruins."
	var image_material := ShaderMaterial.new();image_material.shader = load("res://scripts/rounded_image.gdshader");unlock_art.material = image_material;panel.add_child(unlock_art)
	close_button = _button("×",panel);close_button.accessibility_name = "Close";close_button.pressed.connect(dismiss)
	for label in [clear_caption,price_label]:
		var price_font := Typography.body();price_font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):900};label.add_theme_font_override("font",price_font);label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	cancel.pressed.connect(dismiss)
	clear_button.pressed.connect(func():
		if busy or clear_button.disabled: return
		if unlock_popup: unlock_go_requested.emit()
		elif reveal_confirmation: reveal_confirmed.emit()
		else: confirmed.emit(str(patch.get("id",""))))
	samples = HBoxContainer.new();samples.mouse_filter = Control.MOUSE_FILTER_STOP;add_child(samples)
	for value in ["normal","pressed","disabled","selected"]:
		var button := _button(value.capitalize(),samples)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(func(): sample = value; refresh(state); layout(area))
	hide()

func _button(text: String, parent: Node) -> Button:
	var button := Button.new();button.text = text
	var body := Typography.body();body.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):850};button.add_theme_font_override("font",body)
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: button.add_theme_color_override(key,Color("633b21"))
	parent.add_child(button)
	return button

func open(value: Dictionary, snapshot: Dictionary) -> void:
	unlock_popup = false;reveal_confirmation = false;panel.show();panel.accessibility_name = "Garbage clearance"
	focused_before = get_viewport().gui_get_focus_owner();patch = value.duplicate(true);destination = "";state = snapshot;busy = false
	title.text = "Clear this patch?";cancel.text = "Cancel";cancel.accessibility_name = "Cancel garbage clearance"
	preview.entry = patch;preview.accessibility_name = str(patch.name);show();refresh(snapshot);layout(area);cancel.grab_focus()

func open_destination(name: String, snapshot: Dictionary) -> void:
	unlock_popup = false;reveal_confirmation = false;panel.show();panel.accessibility_name = name
	focused_before = get_viewport().gui_get_focus_owner();destination = name;patch = {"art_id":"submarine-yellow" if name == "Submarine" else "workshop-hut","landmark":true,"name":name};state = snapshot;busy = false
	title.text = name;cancel.text = "Back to restaurant";cancel.accessibility_name = cancel.text;preview.entry = patch;preview.accessibility_name = name;show();refresh(snapshot);layout(area);cancel.grab_focus()

func open_reveal(snapshot: Dictionary) -> void:
	unlock_popup = false;panel.show();focused_before = get_viewport().gui_get_focus_owner();patch = {};destination = "";state = snapshot;busy = false;reveal_confirmation = true
	title.text = "reveal?";panel.accessibility_name = "Reveal confirmation";cancel.text = "Cancel";cancel.accessibility_name = "Cancel reveal"
	preview.entry = {};preview.accessibility_name = "";show();refresh(snapshot);layout(area);cancel.grab_focus()

func hold_for_reveal() -> void:
	# Keep one full-screen input shield alive until both the cover and its frame
	# have gone. The controller opens the same shared presentation afterward.
	busy = true;panel.hide();samples.hide()

func open_unlock(snapshot: Dictionary) -> void:
	if not busy: focused_before = get_viewport().gui_get_focus_owner()
	patch = {};destination = "";state = snapshot;busy = false;reveal_confirmation = false;unlock_popup = true
	panel.show();title.text = "Exhibition Unlocked";panel.accessibility_name = title.text
	preview.entry = {};show();refresh(snapshot);layout(area);clear_button.grab_focus()

func refresh(snapshot: Dictionary) -> void:
	state = snapshot
	if not visible: return
	unlock_art.visible = unlock_popup;close_button.visible = unlock_popup;cancel.visible = not unlock_popup
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT if unlock_popup else HORIZONTAL_ALIGNMENT_CENTER
	clear_button.visible = destination.is_empty()
	well.visible = not reveal_confirmation and not unlock_popup
	price_label.visible = not reveal_confirmation and not unlock_popup;price_coin.visible = not reveal_confirmation and not unlock_popup
	clear_caption.text = "Let's go" if unlock_popup else "Reveal" if reveal_confirmation else "Clear"
	price_label.text = str(int(patch.get("price",0)))
	clear_button.accessibility_name = "Clear for %s coins" % int(patch.get("price",0))
	clear_button.disabled = busy or sample == "disabled" or int(snapshot.get("coins",0)) < int(patch.get("price",0))
	if reveal_confirmation:
		clear_button.accessibility_name = "Reveal"
		clear_button.disabled = busy or sample == "disabled" or not snapshot.get("expansion",{}).get("dock_ready",false)
	if unlock_popup:
		clear_button.accessibility_name = "Let's go";clear_button.disabled = busy
	close_button.disabled = busy
	cancel.disabled = busy
	if area.size.x > 0: _layout_price(area.size.x/390.0)
	preview.queue_redraw()

func dismiss() -> void:
	if busy: return
	hide();closed.emit()
	if is_instance_valid(focused_before) and focused_before.is_visible_in_tree(): focused_before.grab_focus()

func finish_clear(seconds := .26) -> void:
	busy = true;panel.hide();samples.hide()
	# Shield the closing overlay through the world removal transition.
	await get_tree().create_timer(seconds).timeout
	hide();panel.show();busy = false;closed.emit()
	if is_instance_valid(focused_before) and focused_before.is_visible_in_tree(): focused_before.grab_focus()

func layout(value: Rect2) -> void:
	area = value
	if panel == null or area.size.x <= 0: return
	var physical := maxf(.001,get_viewport_transform().get_scale().x)
	var compact := size.y*physical < 600
	if unlock_popup: _layout_unlock(physical,compact);return
	title.autowrap_mode = TextServer.AUTOWRAP_OFF;title.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	for button in samples.get_children(): button.show()
	var unit := area.size.x/390.0
	var height := (220.0 if compact else 276.0)*unit
	var action_height := maxf(48.0/physical,48.0*unit)
	height = maxf(height,action_height+138*unit)
	if reveal_confirmation: height = maxf(154*unit,action_height+78*unit)
	panel.position = Vector2(area.position.x+14*unit,maxf(area.position.y+8*unit,area.end.y-height-(14 if compact else 24)*unit))
	panel.size = Vector2(area.size.x-28*unit,height)
	var shadow := PopupSkin.flat(Color.TRANSPARENT,25*unit);shadow.shadow_color = Color(.35,.18,.05,.24);shadow.shadow_size = int(7*unit);shadow.shadow_offset = Vector2(0,5)*unit
	panel.add_theme_stylebox_override("panel",shadow);PopupSkin.layout_face(face,panel.size,unit*390.0/720.0);face.material.set_shader_parameter("corner_radius",25*unit)
	title.add_theme_font_size_override("font_size",maxi(1,int((22 if compact else 25)*unit)))
	title.position = Vector2(12,18 if compact else 20)*unit;title.size = Vector2(panel.size.x-24*unit,34*unit)
	well.position = Vector2(14,54 if compact else 62)*unit
	well.size = Vector2(panel.size.x-28*unit,maxf(52*unit,panel.size.y-well.position.y-action_height-36*unit))
	well.add_theme_stylebox_override("panel",PopupSkin.flat(Color("fff1d3"),18*unit))
	preview.position = Vector2(14,12)*unit;preview.size = well.size-Vector2(28,24)*unit;preview.queue_redraw()
	var gap := 12*unit
	var available := panel.size.x-28*unit-gap
	cancel.position = Vector2(14*unit,panel.size.y-action_height-18*unit)
	cancel.size = Vector2(available*.9/2.2,action_height)
	clear_button.position = Vector2(cancel.position.x+cancel.size.x+gap,cancel.position.y)
	clear_button.size = Vector2(available*1.3/2.2,action_height)
	if not destination.is_empty(): cancel.size.x = panel.size.x-28*unit
	for button in [cancel,clear_button]:
		button.custom_minimum_size = Vector2.ONE*44.01/physical
		button.add_theme_font_size_override("font_size",maxi(1,int(17*unit)))
		for treatment in ["normal","hover","pressed","disabled"]:
			var primary: bool = button == clear_button
			var style := PopupSkin.flat(Color("ff624b") if primary else Color("fff1d5"),26*unit)
			if treatment == "pressed" or (primary and sample == "pressed"): style.bg_color = style.bg_color.darkened(.06)
			if treatment == "disabled" and primary: style.bg_color = Color("dfc6a1")
			style.shadow_color = Color("bd4528") if primary else Color("b98450");style.shadow_size = maxi(1,int(unit));style.shadow_offset = Vector2(0,1 if treatment == "pressed" else 3)*unit
			button.add_theme_stylebox_override(treatment,style)
		for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: button.add_theme_color_override(key,Color("fff9ed") if button == clear_button else Color("633b21"))
		button.add_theme_color_override("font_disabled_color",Color("705b43"))
		var focus := PopupSkin.flat(Color.TRANSPARENT,26*unit);focus.set_border_width_all(maxi(1,int(2*unit)));focus.border_color = Color("32636b");button.add_theme_stylebox_override("focus",focus)
	samples.visible = gallery and not busy
	samples.position = Vector2(area.position.x+14*unit,area.position.y+86*unit);samples.size = Vector2(area.size.x-28*unit,44.01/physical)
	for button in samples.get_children(): button.custom_minimum_size = Vector2(44.01,44.01)/physical;button.add_theme_font_size_override("font_size",maxi(1,int(12*unit)))
	if sample == "selected": well.add_theme_stylebox_override("panel",PopupSkin.flat(Color("e1ebc6"),18*unit))
	_layout_price(unit)

func _layout_unlock(physical: float, compact: bool) -> void:
	# Phone pixels scale as one native control family. A wider desktop window
	# retains the approved contained card rather than expanding its wood grain.
	var unit := area.size.x/390.0
	if size.x > size.y: unit = minf(unit,1.0/physical)
	if compact: unit = 1.0/physical
	var card_width := area.size.x-28*unit
	if size.x > size.y: card_width = minf(card_width,(296.0 if compact else 412.0)*unit)
	var inset := (12.0 if compact else 14.0)*unit
	close_button.custom_minimum_size = Vector2.ZERO
	PopupSkin.close_button(close_button,maxf(44*unit,44.01/physical)/96.0,physical)
	var close_size: Vector2 = close_button.size
	var heading_size := maxi(1,int(maxf(21.0/physical,(21.0 if compact else 23.4)*unit)))
	title.add_theme_font_size_override("font_size",heading_size)
	# Clear the previous unwrapped label's cached minimum before establishing
	# the narrow header width, then assign the requested heading into it.
	title.text = ""
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title.position = Vector2(inset+2*unit,(10.0 if compact else 16.0)*unit)
	title.size = Vector2(maxf(1,card_width-2*inset-close_size.x-14*unit),0)
	title.text = "Exhibition Unlocked"
	var header_height := maxf(close_size.y,title.get_minimum_size().y)
	var art_width := card_width-2*inset
	var art_height := art_width*2.0/3.0
	var top := (10.0 if compact else 16.0)*unit
	var header_gap := (10.0 if compact else 16.0)*unit
	var action_gap := (12.0 if compact else 18.0)*unit
	var bottom := (14.0 if compact else 20.0)*unit
	var action_height := maxf((44.0 if compact else 48.0)*unit,44.01/physical)
	var height := top+header_height+header_gap+art_height+action_gap+action_height+bottom
	panel.position = Vector2(area.get_center().x-card_width*.5,area.get_center().y-height*.5)
	panel.size = Vector2(card_width,height)
	var shadow := PopupSkin.flat(Color.TRANSPARENT,25*unit);shadow.shadow_color = Color(.35,.18,.05,.24);shadow.shadow_size = int(7*unit);shadow.shadow_offset = Vector2(0,5)*unit
	panel.add_theme_stylebox_override("panel",shadow);PopupSkin.layout_face(face,panel.size,unit*390.0/720.0);face.material.set_shader_parameter("corner_radius",25*unit)
	title.size.y = header_height;title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	close_button.position = Vector2(panel.size.x-inset-close_size.x,top)
	unlock_art.position = Vector2(inset,top+header_height+header_gap);unlock_art.size = Vector2(art_width,art_height)
	unlock_art.material.set_shader_parameter("surface_size",unlock_art.size);unlock_art.material.set_shader_parameter("corner_radius",16*unit)
	clear_button.custom_minimum_size = Vector2.ZERO
	clear_button.position = Vector2(inset,unlock_art.position.y+art_height+action_gap);clear_button.size = Vector2(art_width,action_height)
	clear_button.custom_minimum_size = Vector2.ONE*44.01/physical
	for treatment in ["normal","hover","pressed","disabled"]:
		var pressed: bool = treatment == "pressed" or sample == "pressed"
		var style := PopupSkin.flat(Color("ff624b").darkened(.06) if pressed else Color("ff624b"),26*unit)
		style.shadow_color = Color("bd4528");style.shadow_size = maxi(1,int(unit));style.shadow_offset = Vector2(0,1 if pressed else 3)*unit
		clear_button.add_theme_stylebox_override(treatment,style)
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: clear_button.add_theme_color_override(key,Color("fff9ed"))
	for button in [clear_button,close_button]:
		var focus := PopupSkin.flat(Color.TRANSPARENT,(26.0 if button == clear_button else 22.0)*unit);focus.set_border_width_all(maxi(1,int(2*unit)));focus.border_color = Color("32636b");button.add_theme_stylebox_override("focus",focus)
	clear_caption.add_theme_font_size_override("font_size",maxi(1,int((18.0 if compact else 20.0)*unit)))
	clear_caption.add_theme_color_override("font_color",Color("fff9ed"));clear_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER;clear_caption.position = Vector2.ZERO;clear_caption.size = clear_button.size
	samples.visible = gallery and not busy and not compact
	samples.position = Vector2(area.position.x+14*unit,area.position.y+86*unit);samples.size = Vector2(area.size.x-28*unit,44.01/physical)
	for button in samples.get_children():
		button.visible = button.text in ["Normal","Pressed"];button.custom_minimum_size = Vector2.ONE*44.01/physical;button.add_theme_font_size_override("font_size",maxi(1,int(12*unit)))
		var selected: bool = button.text.to_lower() == sample
		for treatment in ["normal","hover","pressed","disabled"]:
			var style := PopupSkin.flat(Color("99552d") if selected else Color("fff1d5"),16*unit)
			style.shadow_color = Color("b98450");style.shadow_offset = Vector2(0,1 if treatment == "pressed" else 3)*unit
			button.add_theme_stylebox_override(treatment,style)
		for color in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: button.add_theme_color_override(color,Color("fff5df") if selected else Color("633b21"))

func _layout_price(unit: float) -> void:
	if clear_caption == null: return
	var pixels := maxi(1,int(17*unit))
	for label in [clear_caption,price_label]:
		label.add_theme_font_size_override("font_size",pixels);label.add_theme_color_override("font_color",Color("705b43") if clear_button.disabled else Color("fff9ed"))
	if unlock_popup: return
	if reveal_confirmation:
		clear_caption.position = Vector2.ZERO;clear_caption.size = clear_button.size;clear_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER;return
	clear_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	var font: Font = clear_caption.get_theme_font("font")
	var caption_width := font.get_string_size("Clear",HORIZONTAL_ALIGNMENT_LEFT,-1,pixels).x
	var price_width := font.get_string_size(price_label.text,HORIZONTAL_ALIGNMENT_LEFT,-1,pixels).x
	var left := (clear_button.size.x-caption_width-price_width-33*unit)/2
	clear_caption.position = Vector2(left,0);clear_caption.size = Vector2(caption_width,clear_button.size.y)
	price_coin.position = Vector2(left+caption_width+8*unit,(clear_button.size.y-20*unit)/2);price_coin.size = Vector2.ONE*20*unit
	price_label.position = Vector2(price_coin.position.x+25*unit,0);price_label.size = Vector2(price_width,clear_button.size.y)
	price_coin.modulate = Color(.7,.65,.55,.8) if clear_button.disabled else Color.WHITE

func cancel_interactions() -> void:
	for button in [cancel,clear_button,close_button]:
		var disabled: bool = button.disabled;button.disabled = true;button.disabled = disabled

func _input(event: InputEvent) -> void:
	if not visible: return
	if busy:
		get_viewport().set_input_as_handled();return
	if event.is_action_pressed("ui_cancel"):
		dismiss();get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
		var buttons: Array = [close_button] if unlock_popup else [cancel]
		if clear_button.visible and not clear_button.disabled: buttons.append(clear_button)
		if samples.visible: buttons.append_array(samples.get_children().filter(func(button):return button.visible and not button.disabled))
		var index := buttons.find(get_viewport().gui_get_focus_owner())
		buttons[posmod(index+(-1 if event.shift_pressed else 1),buttons.size())].grab_focus()
		get_viewport().set_input_as_handled()
