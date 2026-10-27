extends Control
## Native applicant fan and deferred visibility acknowledgements for People.
const Resume = preload("res://scripts/staff_resume.gd")
const Typography = preload("res://scripts/typography.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const Wood = preload("res://scripts/wood_skin.gd")
signal command_requested(value: Dictionary)
var state: Dictionary = {}
var scene := Rect2()
var unit := 1.0
var safe_top := 0.0
var interaction_blocked := false
var reduced_motion := false
var modal: ColorRect
var panel: Panel
var maple: TextureRect
var title: Label
var subtitle: RichTextLabel
var close_button: Button
var refresh_button: Button
var refresh_title: Label
var refresh_note: Label
var fan: Control
var empty_label: Label
var view := ""
var cards: Dictionary = {}
var offers_signature := ""
var active := 0
var position_value := 0.0
var velocity := 0.0
var target := 0.0
var settling := false
var pitch := 280.0
var pointer := -1
var pointer_start := Vector2.ZERO
var screen_press := Vector2.ZERO
var pointer_position := 0.0
var pointer_last := 0.0
var pointer_time := 0.0
var pointer_velocity := 0.0
var dragged := false
var pointer_axis := ""
var focus_before: Control
var last_hired := ""
var hire_time := -1.0
var hero
var hero_origin := Vector2.ZERO
var viewed_chefs: Dictionary = {}
var people_tray_open := false
var tray_source
var recipe_overlay
var font: Font
var wood = Wood.new()
var closing := false
var keyboard_navigation := false

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);mouse_filter=MOUSE_FILTER_IGNORE
	font=Typography.body();font.variation_opentype={TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	modal=ColorRect.new();modal.color=Color(.24,.18,.1,.28);modal.mouse_filter=MOUSE_FILTER_STOP;modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(modal)
	panel=Panel.new();panel.mouse_filter=MOUSE_FILTER_STOP;modal.add_child(panel)
	maple=TextureRect.new();maple.texture=wood.texture("wood-grain");maple.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;maple.mouse_filter=MOUSE_FILTER_IGNORE
	var material_value:=ShaderMaterial.new();material_value.shader=preload("res://scripts/maple_face.gdshader");maple.material=material_value;panel.add_child(maple)
	title=label(panel);close_button=button("×","Close applicants",panel);close_button.pressed.connect(dismiss)
	subtitle=RichTextLabel.new();subtitle.bbcode_enabled=true;subtitle.scroll_active=false;subtitle.mouse_filter=MOUSE_FILTER_IGNORE;subtitle.add_theme_font_override("normal_font",font);panel.add_child(subtitle)
	fan=Control.new();fan.clip_contents=true;fan.mouse_filter=MOUSE_FILTER_STOP;modal.add_child(fan);fan.gui_input.connect(_fan_gui)
	empty_label=label(fan);empty_label.text="No applications left\n\nRefresh for three new faces.";empty_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;empty_label.hide()
	refresh_button=button("Refresh","Refresh applications",panel);refresh_button.pressed.connect(func():command_requested.emit({"type":"refresh_applicants","now":Time.get_unix_time_from_system()}))
	refresh_title=label(panel);refresh_title.text="Fresh faces?";refresh_note=label(panel)
	modal.hide()

func label(parent: Node) -> Label:
	var result:=Label.new();result.mouse_filter=MOUSE_FILTER_IGNORE;result.add_theme_font_override("font",font);result.add_theme_color_override("font_color",Color("592c10"));parent.add_child(result);return result
func button(text: String, accessible: String, parent: Node) -> Button:
	var result:=Button.new();result.text=text;result.accessibility_name=accessible;result.add_theme_font_override("font",font);result.mouse_filter=MOUSE_FILTER_STOP;parent.add_child(result);return result
func style_button(control: Button, primary := false, disabled := false) -> void:
	control.disabled=disabled
	var scale_value:=unit*390.0/720.0
	for treatment in ["normal","hover","pressed","disabled"]: control.add_theme_stylebox_override(treatment,wood.style("hud-live-pressed" if primary and treatment=="pressed" else "hud-live-normal" if primary and treatment!="disabled" else "hud-cream-pressed" if treatment=="pressed" else "hud-cream-normal",scale_value))
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: control.add_theme_color_override(key,Color("fff9ed") if primary else Color("61381e"))
	control.add_theme_color_override("font_disabled_color",Color("927553"));control.add_theme_stylebox_override("focus",StyleBoxEmpty.new());control.add_theme_font_size_override("font_size",maxi(1,int(15*unit)))
	var minimum:=44.01/maxf(.001,get_viewport_transform().get_scale().x);control.custom_minimum_size=Vector2(minimum,minimum)
func text_at(node: Label, box: Rect2, pixels: float) -> void:
	if node.autowrap_mode!=TextServer.AUTOWRAP_OFF:
		node.position=box.position*unit;node.size=box.size*unit;node.add_theme_font_size_override("font_size",int(pixels*unit))
	else:UISkin.layout_caption(node,Rect2(box.position*unit,box.size*unit),int(pixels*unit))
func refresh(value: Dictionary) -> void:
	state=value
	if state.is_empty():return
	_update_people_visibility()
	if modal.visible and view=="applicants":
		var signature:=JSON.stringify(state.staff.offers)
		if signature!=offers_signature:_sync_offers()
		for card in cards.values():card.coins=int(state.coins);card.full=int(state.staff.count)>=int(state.staff.capacity);card.layout()
		layout(scene)

func open_applicants() -> void:
	if state.is_empty():return
	focus_before=get_viewport().gui_get_focus_owner();view="applicants";closing=false;offers_signature="";active=0;position_value=0;target=0;velocity=0;settling=false;modal.modulate.a=1;panel.modulate.a=1;modal.show();fan.show()
	_sync_offers();layout(scene);close_button.grab_focus()
func _sync_offers() -> void:
	var offers:Array=state.staff.offers
	var old_positions:Dictionary={}
	for id in cards:old_positions[id]=cards[id].position
	var old_ids:Array=cards.keys();var old_active:=""
	if active<old_ids.size():old_active=str(old_ids[active])
	var replaced:=not offers.any(func(offer):return cards.has(offer.id))
	var next:=0 if replaced else mini(active,maxi(0,offers.size()-1))
	for i in range(offers.size()):
		if offers[i].id==old_active:next=i
	for id in old_ids:
		if offers.any(func(offer):return offer.id==id):continue
		var card=cards[id];cards.erase(id);card.hire_button.add_theme_stylebox_override("disabled",card.hire_button.get_theme_stylebox("normal"));card.hire_button.disabled=true;card.mouse_filter=MOUSE_FILTER_STOP;card.z_index=30
		if id==last_hired:_play_hired(card)
		else:
			var exit=create_tween().set_parallel(true);exit.tween_property(card,"modulate:a",0.0,.08 if reduced_motion else .21)
			if not reduced_motion:exit.tween_property(card,"position",card.position+Vector2(-18,52)*unit,.21)
			exit.chain().tween_callback(card.queue_free)
	for i in range(offers.size()):
		var offer:Dictionary=offers[i]
		if cards.has(offer.id):continue
		var card=Resume.new();card.offer=offer;card.unit=unit;fan.add_child(card);cards[offer.id]=card
		card.hire_requested.connect(func(id:String):
			last_hired=id;command_requested.emit({"type":"hire_applicant","offer_id":id}))
		card.hire_button.gui_input.connect(_fan_gui)
		card.modulate.a=0;card.motion_offset=Vector2(0,0 if reduced_motion else 34)*unit
		var enter=create_tween();enter.tween_interval(1.08 if hero!=null else .19 if not old_ids.is_empty() else float(i)*.028);enter.tween_property(card,"modulate:a",1.0,.08 if reduced_motion else .28);enter.parallel().tween_property(card,"motion_offset",Vector2.ZERO,.28).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	offers_signature=JSON.stringify(offers);active=next;position_value=next;target=next;velocity=0;settling=false
	last_hired="";_place_cards()
	for id in cards:
		if not old_positions.has(id):continue
		var card=cards[id];var destination:Vector2=card.position-card.motion_offset
		card.motion_offset=Vector2.ZERO if reduced_motion else old_positions[id]-destination
		var flow=create_tween();flow.tween_interval(1.0 if hero!=null else 0);flow.tween_property(card,"motion_offset",Vector2.ZERO,.28).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_place_cards()

func layout(value: Rect2) -> void:
	scene=value
	if not is_node_ready() or not modal.visible or scene.size.x<=0:return
	var physical:=maxf(.001,get_viewport_transform().get_scale().x)
	var narrow:=scene.size.x*physical<350
	unit=scene.size.x/(320.0 if narrow else 390.0)
	var reference_width:=scene.size.x/unit
	var card_height:=304.0 if narrow else 343.0
	var fan_height:=card_height+48.0
	var panel_height:=fan_height+160.0
	var usable_top:=maxf(scene.position.y,safe_top)
	var usable_height:=scene.end.y-usable_top
	var available:=(usable_height-24*unit)/unit
	if panel_height>available:
		# Keep native landscape contained; uniformly reduce the complete family.
		unit*=available/panel_height;reference_width=scene.size.x/unit
	var width:=scene.size.x-24*unit
	panel.position=Vector2(scene.position.x+12*unit,usable_top+(usable_height-panel_height*unit)*.5)
	panel.size=Vector2(width,panel_height*unit)
	var shadow:=StyleBoxFlat.new();shadow.bg_color=Color.TRANSPARENT;shadow.shadow_color=Color(.3,.16,.04,.25);shadow.shadow_size=int(7*unit);shadow.shadow_offset=Vector2(0,5)*unit;shadow.set_corner_radius_all(int(24*unit));panel.add_theme_stylebox_override("panel",shadow)
	maple.size=panel.size;var material_value:ShaderMaterial=maple.material;material_value.set_shader_parameter("surface_size",panel.size);material_value.set_shader_parameter("corner_radius",24*unit);material_value.set_shader_parameter("grain_width",390*unit)
	title.text="Applicants"
	text_at(title,Rect2(16,14,width/unit-80,32),25)
	close_button.position=Vector2(width-60*unit,14*unit);close_button.size=Vector2(44,44)*unit;close_button.accessibility_name="Close applicants";style_button(close_button)
	subtitle.position=Vector2(16,50)*unit;subtitle.size=Vector2(width/unit-75,24)*unit;subtitle.add_theme_font_size_override("normal_font_size",int(12*unit));subtitle.add_theme_color_override("default_color",Color("8a5b34"))
	if view=="applicants":subtitle.text="Staff %s / %s · %s" % [state.staff.count,state.staff.capacity,"[color=#b84432]Roster full[/color]" if int(state.staff.count)>=int(state.staff.capacity) else "%s space%s available" % [int(state.staff.capacity)-int(state.staff.count),"" if int(state.staff.capacity)-int(state.staff.count)==1 else "s"]]
	fan.position=Vector2(scene.position.x,panel.position.y+80*unit);fan.size=Vector2(scene.size.x,fan_height*unit)
	pitch=minf(326,reference_width-72)*.88
	for card in cards.values():
		card.unit=unit;card.narrow=narrow;card.size=Vector2(minf(326,reference_width-72),card_height)*unit;card.pivot_offset=Vector2(card.size.x*.5,card.size.y*.75);card.layout()
	_place_cards()
	empty_label.visible=view=="applicants" and cards.is_empty();empty_label.position=Vector2(24,90)*unit;empty_label.size=Vector2(fan.size.x-48*unit,140*unit);empty_label.add_theme_font_size_override("font_size",int(18*unit))
	refresh_button.visible=view=="applicants";refresh_title.visible=refresh_button.visible;refresh_note.visible=refresh_button.visible
	var bottom:=panel_height-76
	text_at(refresh_title,Rect2(22,bottom+10,width/unit-145,24),14)
	text_at(refresh_note,Rect2(22,bottom+36,width/unit-145,20),10)
	refresh_button.position=Vector2(width-122*unit,(bottom+9)*unit);refresh_button.size=Vector2(102,44)*unit
	var seconds:=maxi(0,int(ceil(float(state.staff.refresh_deadline)-Time.get_unix_time_from_system())))
	refresh_note.text="Available in %02d:%02d" % [seconds/60,seconds%60] if seconds>0 else "Free · replaces remaining offers";style_button(refresh_button,false,seconds>0)

func _place_cards() -> void:
	var index:=0
	for card in cards.values():
		var distance:=float(index)-position_value;var depth:=minf(1,absf(distance))
		card.position=Vector2((fan.size.x-card.size.x)*.5+distance*pitch*unit,(12+depth*20)*unit);card.position+=card.motion_offset;card.rotation=0 if reduced_motion else deg_to_rad(clampf(distance*9,-14,14));card.scale=Vector2.ONE*(1 if reduced_motion else 1-depth*.045);card.z_index=10-int(round(absf(distance)*2))
		card.hire_button.focus_mode=Control.FOCUS_ALL if index==active else Control.FOCUS_NONE
		card.hire_button.mouse_filter=Control.MOUSE_FILTER_STOP if index==active else Control.MOUSE_FILTER_IGNORE
		index+=1

func _play_hired(card) -> void:
	hero=card;hire_time=0;hero_origin=card.position;card.rotation=0;card.pivot_offset=card.size*.5
	card.stamp_prop.modulate.a=0;card.imprint.modulate.a=0
	var paper=create_tween();paper.tween_property(card,"scale",Vector2.ONE*(1 if reduced_motion else 1.045),.08 if reduced_motion else .18).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	paper.tween_interval(.45 if reduced_motion else .79)
	paper.tween_property(card,"modulate:a",0.0,.12 if reduced_motion else .31)
	if not reduced_motion:paper.parallel().tween_property(card,"position",hero_origin+Vector2(-90,-145)*unit,.31).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN);paper.parallel().tween_property(card,"rotation",deg_to_rad(-16),.31)
	paper.chain().tween_callback(func():card.queue_free();hero=null;hire_time=-1)
	var ink=create_tween();ink.tween_interval(.08 if reduced_motion else .405);ink.tween_property(card.imprint,"modulate:a",.94,.08 if reduced_motion else .05)
	if not reduced_motion:
		var contact:Vector2=card.stamp_prop.position;card.stamp_prop.position=contact-Vector2(0,170)*unit
		var prop=create_tween();prop.tween_interval(.19);prop.tween_callback(func():card.stamp_prop.modulate.a=1);prop.tween_property(card.stamp_prop,"position",contact,.215).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN);prop.tween_property(card.stamp_prop,"position",contact-Vector2(0,11)*unit,.07);prop.tween_property(card.stamp_prop,"position",contact-Vector2(0,4)*unit,.06);prop.tween_property(card.stamp_prop,"position",contact-Vector2(0,175)*unit,.20);prop.parallel().tween_property(card.stamp_prop,"modulate:a",0,.20)

func browse(index: int) -> void:
	target=clampf(index,0,maxi(0,cards.size()-1));active=int(target);settling=true
	if reduced_motion:position_value=target;velocity=0;settling=false
	_place_cards()
func _fan_gui(event: InputEvent) -> void:
	if view!="applicants" or closing:return
	if event is InputEventScreenTouch and event.pressed:
		pointer=event.index;pointer_start=screen_press;pointer_position=position_value;pointer_last=position_value;pointer_time=Time.get_ticks_msec()/1000.0;pointer_velocity=0;dragged=false;pointer_axis="";settling=false
	elif event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:browse(active+(-1 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1));get_viewport().set_input_as_handled()
func _input(event: InputEvent) -> void:
	if not modal.visible:return
	if event is InputEventScreenTouch and event.pressed:screen_press=event.position
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_ESCAPE:dismiss();get_viewport().set_input_as_handled();return
		if view=="applicants" and event.keycode in [KEY_LEFT,KEY_RIGHT,KEY_HOME,KEY_END]:browse(0 if event.keycode==KEY_HOME else cards.size()-1 if event.keycode==KEY_END else active+(-1 if event.keycode==KEY_LEFT else 1));get_viewport().set_input_as_handled();return
		if event.keycode==KEY_TAB:
			var controls:Array=[close_button,refresh_button]
			if view=="applicants" and not cards.is_empty():controls.insert(1,cards.values()[active].hire_button)
			controls=controls.filter(func(control):return control.visible and not control.disabled)
			var current:=controls.find(get_viewport().gui_get_focus_owner());controls[posmod(current+(-1 if event.shift_pressed else 1),controls.size())].grab_focus();get_viewport().set_input_as_handled();return
	if pointer<0:return
	if event is InputEventScreenDrag and event.index==pointer:
		var dx:float=event.position.x-pointer_start.x;var dy:float=event.position.y-pointer_start.y
		if pointer_axis=="" and Vector2(dx,dy).length()>6*unit:pointer_axis="x" if absf(dx)>=absf(dy) else "y"
		if pointer_axis=="x":
			if not dragged:
				for card in cards.values():var disabled:bool=card.hire_button.disabled;card.hire_button.disabled=true;card.hire_button.disabled=disabled
				dragged=true
			var next:=pointer_position-dx/(pitch*unit);var maximum:=maxi(0,cards.size()-1)
			if next<0:next=next/(1+absf(next)*3)*.42
			elif next>maximum:var beyond:float=next-maximum;next=maximum+beyond/(1+beyond*3)*.42
			else:next-=sin(next*TAU)*.024
			var now:=Time.get_ticks_msec()/1000.0;pointer_velocity=pointer_velocity*.45+(next-pointer_last)/maxf(.001,now-pointer_time)*.55;pointer_time=now;pointer_last=next;position_value=next;_place_cards()
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch and not event.pressed and event.index==pointer:
		if dragged or event.canceled:
			velocity=0 if event.canceled else clampf(pointer_velocity,-5,5);browse(int(round(clampf(position_value+velocity*.14,0,maxi(0,cards.size()-1)))));get_viewport().set_input_as_handled()
		pointer=-1
func dismiss(immediate := false) -> void:
	if not modal.visible or closing:return
	closing=true;pointer=-1;settling=false
	var finish=func():
		modal.hide();closing=false;view=""
		if is_instance_valid(focus_before) and focus_before.is_visible_in_tree():focus_before.grab_focus()
	if immediate or reduced_motion:finish.call();return
	var exit=create_tween();exit.tween_property(modal,"modulate:a",0.0,.17);exit.tween_callback(finish)
func _process(delta: float) -> void:
	if modal.visible and view=="applicants":
		if settling:
			var step:=minf(delta,1.0/30);velocity+=((target-position_value)*240-velocity*27)*step;position_value+=velocity*step
			if absf(position_value-target)<.0006 and absf(velocity)<.008:position_value=target;velocity=0;settling=false
			_place_cards()
		var seconds:=maxi(0,int(ceil(float(state.staff.refresh_deadline)-Time.get_unix_time_from_system())))
		refresh_note.text="Available in %02d:%02d" % [seconds/60,seconds%60] if seconds>0 else "Free · replaces remaining offers";refresh_button.disabled=seconds>0
	if modal.visible and view=="applicants":_place_cards()
	if hero!=null:hire_time+=delta
	_collect_seen(get_window().has_focus())
func note_viewed(id: String) -> void:
	if people_tray_open and state.get("inventory", []).any(func(item): return item.get("kind") == "chef" and item.get("id") == id and item.get("staff_new", false)):
		viewed_chefs[id] = true

func _collect_seen(foreground_visible: bool) -> void:
	if interaction_blocked or not foreground_visible or not people_tray_open or tray_source == null or not tray_source.is_visible_in_tree() or modal.visible or (recipe_overlay != null and recipe_overlay.visible): return
	var rail_rect: Rect2 = tray_source.rail.get_global_rect()
	for card in tray_source.cards:
		var item: Dictionary = card.get_meta("entry", {})
		if not item.get("staff_new", false): continue
		var bounds: Rect2 = card.get_global_rect()
		if rail_rect.intersection(bounds).get_area()/maxf(.001,bounds.get_area()) >= .85:
			viewed_chefs[item.id] = true

func _update_people_visibility() -> void:
	var was_open := people_tray_open
	var editor: Dictionary = state.get("editor", {})
	people_tray_open = state.get("mode") == "edit" and editor.get("layer") == "people" and editor.get("tray_open", false)
	if was_open and not people_tray_open:
		var ids := viewed_chefs.keys()
		viewed_chefs.clear()
		# Clear before emitting: the saved command refreshes this view synchronously.
		if not ids.is_empty(): command_requested.emit({"type":"staff_seen","ids":ids})

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		pointer=-1;settling=false
		if is_node_ready():
			var controls:Array=[close_button,refresh_button]
			for card in cards.values():controls.append(card.hire_button)
			for control in controls:
				var disabled:bool=control.disabled;control.disabled=true;control.disabled=disabled
