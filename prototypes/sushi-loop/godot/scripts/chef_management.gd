extends Control
## Live management content on the shared maple shell; no separate pale backing.
const Dev=preload("res://scripts/chef_development.gd")
const Book=preload("res://scripts/recipe_book.gd")
const Art=preload("res://scripts/recipe_art.gd")
const Wood=preload("res://scripts/wood_skin.gd")
const Type=preload("res://scripts/typography.gd")
const UISkin=preload("res://scripts/ui_skin.gd")
signal requested(value:Dictionary)
signal firing_requested
signal placement_requested
var actor:Dictionary={}
var state:Dictionary={}
var unit:=1.0
var font:Font
var wood=Wood.new()
var scroll:ScrollContainer
var content:Control
var facts:Array[Label]=[]
var assignment:Label
var tier_label:Label
var ceiling:Label
var next_label:Label
var preview:Label
var unlock:Label
var result:Label
var upgrade:Button
var unassign:Button
var fire:Button
var budget:Label
var current_plate:Control
var next_plate:Control
var expected_level:=0
var last_purchase_ms:=-1000
var upgrade_word:Label
var upgrade_price:Label
var coin:TextureRect
var stat_divider:ColorRect
class Plate extends Control:
	var tier_name:="White"
	func _draw()->void:
		var image:Texture2D=load("res://assets/ui/recipes/plates.png")
		var index:int=preload("res://scripts/recipe_art.gd").TIERS.find(tier_name)
		preload("res://scripts/recipe_art.gd")._draw_cell(self,image,maxi(0,index),Rect2(Vector2.ZERO,size),Color.WHITE)
func _ready()->void:
	mouse_filter=MOUSE_FILTER_STOP
	font=Type.body();font.variation_opentype={TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	scroll=ScrollContainer.new();scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;scroll.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_SHOW_NEVER;scroll.follow_focus=true;add_child(scroll)
	content=Control.new();content.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(content)
	stat_divider=ColorRect.new();stat_divider.color=Color("d4a568");stat_divider.mouse_filter=MOUSE_FILTER_IGNORE;content.add_child(stat_divider)
	assignment=label(content)
	for text in ["Level","Cooking speed","Growth / level"]:
		var name_label:=label(content);name_label.text=text;facts.append(name_label);facts.append(label(content))
	tier_label=label(content);ceiling=label(content);next_label=label(content);preview=label(content);unlock=label(content);result=label(content)
	current_plate=Plate.new();current_plate.mouse_filter=MOUSE_FILTER_IGNORE;content.add_child(current_plate)
	next_plate=Plate.new();next_plate.mouse_filter=MOUSE_FILTER_IGNORE;content.add_child(next_plate)
	upgrade=button("Level up",self);upgrade.pressed.connect(func():
		if not upgrade.disabled and Time.get_ticks_msec()-last_purchase_ms>=300:
			last_purchase_ms=Time.get_ticks_msec();requested.emit({"type":"level_up_chef","chef_id":actor.id,"expected_level":expected_level}))
	upgrade_word=label(upgrade);upgrade_word.text="Level up";upgrade_price=label(upgrade)
	coin=TextureRect.new();var emblem:=AtlasTexture.new();emblem.atlas=wood.texture("coin-emblem");emblem.region=Rect2(32,32,108,108);coin.texture=emblem;coin.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;coin.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;coin.mouse_filter=MOUSE_FILTER_IGNORE;upgrade.add_child(coin)
	unassign=button("Unassign",self);unassign.pressed.connect(func():
		if placed():requested.emit({"type":"unassign_chef","chef_id":actor.id})
		else:placement_requested.emit())
	fire=button("Fire…",self);fire.pressed.connect(func():firing_requested.emit())
	budget=label(self);budget.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;budget.add_theme_color_override("font_color",Color("9d4b33"));result.add_theme_color_override("font_color",Color("4b704e"))
func label(parent:Node)->Label:
	var value:=Label.new();value.add_theme_font_override("font",font);value.add_theme_color_override("font_color",Color("592c10"));value.mouse_filter=MOUSE_FILTER_IGNORE;parent.add_child(value);return value
func button(text:String,parent:Node)->Button:
	var value:=Button.new();value.text=text;value.accessibility_name=text;value.add_theme_font_override("font",font);parent.add_child(value);return value
func placed()->bool:return state.get("objects",[]).any(func(c):return c.get("id")==actor.get("id"))
func refresh(snapshot:Dictionary,chef:Dictionary)->void:
	state=snapshot;actor=chef
	if not is_node_ready() or actor.is_empty():return
	expected_level=int(actor.level)
	assignment.text="Assigned · restaurant" if placed() else "Unassigned staff"
	facts[1].text="%s / %s"%[actor.level,actor.level_cap];facts[3].text="%.2f×"%float(actor.cooking_speed);facts[5].text="+%s%%"%int(round(float(actor.growth_rate)*100))
	current_plate.tier_name=Dev.tier(int(actor.level));current_plate.queue_redraw()
	tier_label.text="%s recipes"%Dev.tier(int(actor.level));ceiling.text="Ceiling: Level %s · %s plates"%[actor.level_cap,Dev.tier(int(actor.level_cap))]
	var maximum:bool=int(actor.level)>=int(actor.level_cap)
	next_label.text="Capability ceiling reached   MAX" if maximum else "Next: Level %s"%(int(actor.level)+1)
	preview.text="Final speed %.2f× · %s recipes"%[actor.cooking_speed,Dev.tier(int(actor.level))] if maximum else "Cooking speed       %.2f×  →  %.2f×"%[actor.cooking_speed,Dev.next_speed(actor)]
	var changes:bool=not maximum and Dev.tier(int(actor.level)+1)!=Dev.tier(int(actor.level))
	unlock.text="Unlocks %s recipes\nAvailable at Level %s"%[Dev.tier(int(actor.level)+1),int(actor.level)+1] if changes else ""
	next_plate.visible=changes;next_plate.tier_name=Dev.tier(int(actor.level)+1);next_plate.queue_redraw()
	upgrade.visible=not maximum;upgrade.disabled=int(state.coins)<Dev.cost(actor);upgrade.text="";upgrade_price.text=str(Dev.cost(actor))
	upgrade.accessibility_name="Level up %s to Level %s for %s coins"%[actor.name,int(actor.level)+1,Dev.cost(actor)]
	budget.text="%s / %s coins · Not enough coins"%[state.coins,Dev.cost(actor)] if not maximum and upgrade.disabled else ""
	unassign.text="Unassign" if placed() else "Place in restaurant";unassign.accessibility_name=unassign.text
	layout(size,unit)
func text_at(node:Label,box:Rect2,pixels:float)->void:
	node.position=box.position*unit;node.size=box.size*unit;node.add_theme_font_size_override("font_size",maxi(1,int(pixels*unit)));node.vertical_alignment=VERTICAL_ALIGNMENT_CENTER;node.horizontal_alignment=HORIZONTAL_ALIGNMENT_LEFT
func style_button(control:Button,primary:bool=false)->void:
	var scale_value:=control.size.y/78.0
	for treatment in ["normal","hover","pressed","disabled"]:control.add_theme_stylebox_override(treatment,wood.style("hud-live-pressed" if primary and treatment=="pressed" else "hud-live-normal" if primary and treatment!="disabled" else "hud-cream-pressed" if treatment=="pressed" else "hud-cream-normal",scale_value))
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:control.add_theme_color_override(key,Color("fff9ed") if primary else Color("61381e"))
	control.add_theme_color_override("font_disabled_color",Color("927553"));control.add_theme_stylebox_override("focus",StyleBoxEmpty.new());control.add_theme_font_size_override("font_size",int(28*unit))
	var hit:=44.01/maxf(.001,get_viewport_transform().get_scale().x);control.custom_minimum_size=Vector2(hit,hit)
func layout(bounds:Vector2,scale_value:float)->void:
	unit=scale_value;size=bounds
	if not is_node_ready() or unit<=0:return
	var h:=size.y/unit;var w:=size.x/unit;var short:=h<700
	var wide:=w>800
	var footer:=108.0 if wide else 235.0
	scroll.position=Vector2.ZERO;scroll.size=Vector2(size.x,maxf(50,(h-footer)*unit));content.custom_minimum_size=Vector2(size.x,maxf(280 if wide else 560,h-footer)*unit);content.size=content.custom_minimum_size
	text_at(assignment,Rect2(36,26,w-72,34),20)
	for i in range(3):
		text_at(facts[i*2],Rect2(36+i*(w-72)/3,94,(w-72)/3,28),18)
		text_at(facts[i*2+1],Rect2(36+i*(w-72)/3,130,(w-72)/3,54),41)
	current_plate.position=Vector2(26,194)*unit;current_plate.size=Vector2(112,112)*unit
	text_at(tier_label,Rect2(142,215,w-176,36),25);text_at(ceiling,Rect2(142,255,w-176,30),18)
	stat_divider.position=Vector2(36,310)*unit;stat_divider.size=Vector2(w-72,1)*unit
	text_at(next_label,Rect2(36,338,w-72,44),28);text_at(preview,Rect2(36,405,w-72,44),26)
	next_plate.position=Vector2(26,466)*unit;next_plate.size=Vector2(108,108)*unit;text_at(unlock,Rect2(142,478,w-178,75),22)
	text_at(result,Rect2(36,563,w-72,50),20)
	var target:=maxf(88*unit,44.01/maxf(.001,get_viewport_transform().get_scale().x))
	upgrade.position=Vector2(36,(h-footer+8))*unit;upgrade.size=Vector2((w-72)*unit,target);style_button(upgrade,true)
	text_at(upgrade_word,Rect2(32,0,w-250,target/unit),32);text_at(upgrade_price,Rect2(w-176,0,90,target/unit),32)
	upgrade_word.add_theme_color_override("font_color",Color("927553") if upgrade.disabled else Color("fff9ed"));upgrade_price.add_theme_color_override("font_color",Color("927553") if upgrade.disabled else Color("fff9ed"));upgrade_price.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT
	coin.position=Vector2((w-224)*unit,(target-40*unit)*.5);coin.size=Vector2(40,40)*unit
	text_at(budget,Rect2(36,h-footer+108,w-72,30),20);budget.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	unassign.position=Vector2(36*unit,size.y-target-24*unit);unassign.size=Vector2((w-210)*unit,target);style_button(unassign)
	fire.position=Vector2((w-154)*unit,size.y-target-24*unit);fire.size=Vector2(120*unit,target);style_button(fire)
	for treatment in ["normal","hover","pressed","disabled"]:fire.add_theme_stylebox_override(treatment,StyleBoxEmpty.new())
	for key in ["font_color","font_hover_color","font_pressed_color"]:fire.add_theme_color_override(key,Color("ad4835"))
	if wide:
		var column:=(w-108)*.5
		text_at(assignment,Rect2(36,12,column,30),18)
		for i in range(3):
			text_at(facts[i*2],Rect2(36+i*column/3,60,column/3,26),17);text_at(facts[i*2+1],Rect2(36+i*column/3,92,column/3,42),32)
		current_plate.position=Vector2(24,132)*unit;current_plate.size=Vector2(100,100)*unit
		text_at(tier_label,Rect2(132,151,column-100,34),23);text_at(ceiling,Rect2(132,191,column-100,30),16)
		text_at(next_label,Rect2(w*.5+18,12,column,40),27);text_at(preview,Rect2(w*.5+18,66,column,44),22)
		next_plate.position=Vector2(w*.5+8,120)*unit;next_plate.size=Vector2(100,100)*unit
		text_at(unlock,Rect2(w*.5+124,137,column-106,72),20);text_at(result,Rect2(36,240,w-72,30),18)
		stat_divider.position=Vector2(w*.5,18)*unit;stat_divider.size=Vector2(1,207)*unit
		upgrade.position=Vector2(36*unit,size.y-target-10*unit);upgrade.size=Vector2((w*.5-54)*unit,target)
		text_at(upgrade_word,Rect2(24,0,upgrade.size.x/unit-170,target/unit),28);text_at(upgrade_price,Rect2(upgrade.size.x/unit-102,0,72,target/unit),28);upgrade_price.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT
		coin.position=Vector2(upgrade.size.x-156*unit,(target-36*unit)*.5);coin.size=Vector2(36,36)*unit
		unassign.position=Vector2((w*.5+18)*unit,size.y-target-10*unit);unassign.size=Vector2((w*.5-190)*unit,target)
		fire.position=Vector2((w-154)*unit,size.y-target-10*unit);fire.size=Vector2(120*unit,target)
		text_at(budget,Rect2(36,h-footer-32,w*.5-54,28),18)
	queue_redraw()
func _draw()->void:
	if not is_node_ready():return
	var y:=size.y-128*unit
	if size.y/unit>=700:draw_line(Vector2(36*unit,y),Vector2(size.x-36*unit,y),Color("d4a568"),unit)
