extends Control
## Named application confirmation. Removal commits before prop/ink presentation.
const Resume=preload("res://scripts/staff_resume.gd")
const Wood=preload("res://scripts/wood_skin.gd")
const Type=preload("res://scripts/typography.gd")
signal confirmed
signal canceled
signal closed
var reduced_motion:=false
var fired:=false
var actor:Dictionary={}
var unit:=1.0
var wood=Wood.new()
var panel:Panel
var maple:TextureRect
var heading:Label
var close_button:Button
var cancel_button:Button
var confirm_button:Button
var resume
var entry_tween:Tween
var stamp_tween:Tween
var prop_tween:Tween
var font:Font
var resting:=Vector2.ZERO
var area:=Rect2()
func _ready()->void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);mouse_filter=MOUSE_FILTER_STOP
	font=Type.body();font.variation_opentype={TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	var scrim:=ColorRect.new();scrim.color=Color(.24,.18,.1,.28);scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);scrim.mouse_filter=MOUSE_FILTER_STOP;add_child(scrim)
	panel=Panel.new();panel.mouse_filter=MOUSE_FILTER_STOP;add_child(panel)
	maple=TextureRect.new();maple.texture=wood.texture("wood-grain");maple.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;maple.mouse_filter=MOUSE_FILTER_IGNORE
	var material_value:=ShaderMaterial.new();material_value.shader=preload("res://scripts/maple_face.gdshader");maple.material=material_value;panel.add_child(maple)
	heading=Label.new();heading.add_theme_font_override("font",font);heading.add_theme_color_override("font_color",Color("592c10"));panel.add_child(heading)
	close_button=button("×",panel);close_button.pressed.connect(back)
	resume=Resume.new();resume.dismissal_mode=true;panel.add_child(resume)
	cancel_button=button("Cancel",panel);cancel_button.pressed.connect(back)
	confirm_button=button("Fire",panel);confirm_button.pressed.connect(func():
		if not fired:confirmed.emit())
	hide()
func button(text:String,parent:Node)->Button:
	var control:=Button.new();control.text=text;control.accessibility_name=text;control.add_theme_font_override("font",font);parent.add_child(control);return control
func style(control:Button,primary:=false)->void:
	for treatment in ["normal","hover","pressed","disabled"]:control.add_theme_stylebox_override(treatment,wood.style("hud-live-pressed" if primary and treatment=="pressed" else "hud-live-normal" if primary else "hud-cream-pressed" if treatment=="pressed" else "hud-cream-normal",unit*390/720))
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:control.add_theme_color_override(key,Color("fff9ed") if primary else Color("61381e"))
	control.add_theme_stylebox_override("focus",StyleBoxEmpty.new());control.add_theme_font_size_override("font_size",int(16*unit));var hit:=44.01/maxf(.001,get_viewport_transform().get_scale().x);control.custom_minimum_size=Vector2(hit,hit)
func open(value:Dictionary,bounds:Rect2)->void:
	stop_motion();actor=value.duplicate(true);fired=false
	var data:Dictionary={}
	for applicant in preload("res://scripts/staff_book.gd").definition().applicants.values():
		if applicant.art_id==actor.art_id:data=applicant.duplicate(true)
	var identities:={"chef-lena":{"role":"School-kitchen lead · Bristol","background":"Black British · patient, practical, and happiest cooking for a crowd","name":"Lena Brooks"},"chef-omar":{"role":"Former bakery owner · Amman","background":"Jordanian American · patient baker and weekend jazz listener","name":"Omar Haddad"}}
	if data.is_empty():data=identities.get(actor.art_id,{"name":actor.name,"role":"Restaurant chef","background":""}).duplicate(true)
	if actor.has("full_name"):data.name=actor.full_name
	elif str(data.get("name","")).get_slice(" ",0)!=str(actor.name):data={"name":actor.name,"role":"Restaurant chef","background":""}
	for key in ["level","level_cap","growth_rate","cooking_speed","art_id"]:data[key]=actor[key]
	data.id=actor.id;data.cost=0;resume.offer=data;resume.stamp_text.text="Fired";resume.imprint.modulate.a=0;resume.stamp_prop.modulate.a=0
	heading.text="Fire %s?"%actor.name;resume.dismissal_note.text="%s will permanently leave your staff, including their level and upgrades."%data.name
	confirm_button.text="Fire %s"%actor.name;confirm_button.accessibility_name=confirm_button.text;cancel_button.text="Cancel";cancel_button.show();confirm_button.show();close_button.accessibility_name="Cancel dismissal"
	show();layout(bounds);close_button.grab_focus();panel.modulate.a=0
	if is_instance_valid(entry_tween):entry_tween.kill()
	panel.position=resting if reduced_motion else resting+Vector2(0,bounds.size.y)
	entry_tween=create_tween().set_parallel(true);entry_tween.tween_property(panel,"position",resting,.10 if reduced_motion else .34).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT);entry_tween.tween_property(panel,"modulate:a",1.0,.10 if reduced_motion else .34)
func layout(bounds:Rect2)->void:
	var resized:=area.has_area() and area!=bounds
	if resized:
		stop_motion();panel.modulate.a=1
		resume.imprint.modulate.a=.94 if fired else 0;resume.stamp_prop.modulate.a=0
	area=bounds
	if not is_node_ready() or not visible:return
	var physical:=maxf(.001,get_viewport_transform().get_scale().x)
	unit=minf(bounds.size.x/390.0,1.0/physical) if bounds.size.y*physical<500 else bounds.size.x/390.0
	var h:=minf(580.0,(bounds.size.y-24*unit)/unit)
	panel.size=Vector2(bounds.size.x-24*unit,h*unit);resting=Vector2(bounds.position.x+12*unit,bounds.position.y+(bounds.size.y-panel.size.y)*.5)
	if not is_instance_valid(entry_tween) or not entry_tween.is_running():panel.position=resting
	var shadow:=StyleBoxFlat.new();shadow.bg_color=Color.TRANSPARENT;shadow.shadow_color=Color(.3,.16,.04,.25);shadow.shadow_size=int(7*unit);shadow.shadow_offset=Vector2(0,5)*unit;shadow.set_corner_radius_all(int(24*unit));panel.add_theme_stylebox_override("panel",shadow)
	maple.size=panel.size;var material_value:ShaderMaterial=maple.material;material_value.set_shader_parameter("surface_size",panel.size);material_value.set_shader_parameter("corner_radius",24*unit);material_value.set_shader_parameter("grain_width",390*unit)
	heading.position=Vector2(16,18)*unit;heading.size=Vector2(panel.size.x-80*unit,38*unit);heading.add_theme_font_size_override("font_size",int(23*unit))
	close_button.position=Vector2(panel.size.x-58*unit,12*unit);close_button.size=Vector2(44,44)*unit;style(close_button)
	resume.compact_dismissal=h<450
	resume.unit=unit;resume.narrow=bounds.size.x*get_viewport_transform().get_scale().x<350;resume.position=Vector2(18,76)*unit;resume.size=Vector2(panel.size.x-36*unit,(h-154)*unit);resume.layout()
	var button_y:=panel.size.y-64*unit
	cancel_button.position=Vector2(18*unit,button_y);cancel_button.size=Vector2((panel.size.x-46*unit)*.5,46*unit)
	confirm_button.position=Vector2(panel.size.x*.5+5*unit,button_y);confirm_button.size=cancel_button.size
	if fired:cancel_button.position.x=18*unit;cancel_button.size.x=panel.size.x-36*unit
	style(cancel_button);style(confirm_button,true)
func play_fired()->void:
	if fired:return
	fired=true;heading.text="Application";cancel_button.text="Close";cancel_button.accessibility_name="Close fired application";close_button.accessibility_name="Close fired application";confirm_button.hide()
	resume.dismissal_note.text="%s has left your staff."%resume.offer.name
	layout(area);close_button.grab_focus()
	if is_instance_valid(stamp_tween):stamp_tween.kill()
	stamp_tween=create_tween();stamp_tween.tween_interval(.0 if reduced_motion else .35);stamp_tween.tween_property(resume.imprint,"modulate:a",.94,.18 if reduced_motion else .05)
	if not reduced_motion:
		var contact:Vector2=resume.stamp_prop.position;resume.stamp_prop.position=contact-Vector2(0,170)*unit
		prop_tween=create_tween();var prop:=prop_tween;prop.tween_interval(.17);prop.tween_callback(func():resume.stamp_prop.modulate.a=1);prop.tween_property(resume.stamp_prop,"position",contact,.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN);prop.tween_property(resume.stamp_prop,"position",contact-Vector2(0,11)*unit,.07);prop.tween_property(resume.stamp_prop,"position",contact-Vector2(0,4)*unit,.06);prop.tween_property(resume.stamp_prop,"position",contact-Vector2(0,175)*unit,.22);prop.parallel().tween_property(resume.stamp_prop,"modulate:a",0,.22)
func stop_motion()->void:
	for tween in [entry_tween,stamp_tween,prop_tween]:
		if is_instance_valid(tween):tween.kill()
func back()->void:
	stop_motion();hide()
	if fired:closed.emit()
	else:canceled.emit()
func targets()->Array[Control]:
	var result:Array[Control]=[close_button,cancel_button]
	if not fired:result.append(confirm_button)
	return result
