extends Control

const Restaurant = preload("res://scripts/restaurant_model.gd")
const Save = preload("res://scripts/save_store.gd")
const Audio = preload("res://scripts/sound.gd")
const INK := Color("293c3f")
const PAPER := Color("fff4d9")
const CORAL := Color("df7964")
const MINT := Color("92bca6")
const GOLD := Color("efc56a")
const NAVY := Color("143743")
const TIERS := ["Wood", "Steel", "Copper", "Silver", "Gold"]
const CELL := 81.0
const ORIGIN := Vector2(75, 235)
var model = Restaurant.new()
var audio: Node
var branding: Dictionary
var balance: Dictionary
var meta := {"charge":1.0,"salvage":0,"upgrades":{"hull":0,"harpoon":0,"collector":0},"intro_seen":false,"tutorial":0,"dives":0,"new_recipes":[],"completed":[],"sound":true,"music":true,"haptics":true,"reduced_motion":false,"pending_coins":0.0,"floor_style":0}
var screen := "loading"
var modal := ""
var return_screen := "restaurant"
var clock := 0.0
var scene_time := 0.0
var autosave := 0.0
var textures: Dictionary = {}
var font: Font = ThemeDB.fallback_font
var display: Font = ThemeDB.fallback_font
var buttons: Array = []
var editing := false
var selected := -1
var selected_recipe := "cucumber"
var selected_route := 0
var inventory_kind := ""
var layer := 1
var pan := Vector2.ZERO
var pointer_start := Vector2.ZERO
var pointer_last := Vector2.ZERO
var moving := false
var dragged := false
var drag_kind := ""
var pressed_action := ""
var pressed_data: Variant
var toast := ""
var toast_time := 0.0
var pops: Array = []
var dive: Control
var result: Dictionary = {}
var restored_dive: Dictionary = {}
var backgrounded := false
var background_stamp := 0.0
var load_progress := 0
var load_assets := ["chef","customer_1","customer_2","customer_3","customer_4","submarine","cucumber","salmon","shrimp","eel","creature_salmon","creature_shrimp","creature_eel","gear","rock","portal","plant","lantern","icon","cover","title_vignette","results_complete","results_early","results_failed","crate","rubble","customer_walk_1","customer_walk_2","customer_walk_3","restaurant_environment","ocean_environment","rubble_cluster","blackboard","paper_panel","coral_panel","expedition_card","belt_material","seat","chef_2"]
var path_start := -1
var last_path := -1
var sale_ping := 0.0
var board_shake := 0.0
var drawing_offset := Vector2.ZERO

func _extra_height() -> float:
	return maxf(0.0,size.y-1280.0)

func _frame_origin() -> Vector2:
	return Vector2(maxf(0,size.x-720.0)/2,_extra_height()/2)

func _restaurant_origin() -> Vector2:
	return Vector2(maxf(0,size.x-720.0)/2,0)

func _screen_position(point:Vector2) -> Vector2:
	return point+(_restaurant_origin() if screen=="restaurant" and modal=="" else _frame_origin())

func _grid_step() -> Vector2:
	return Vector2(CELL,CELL+_extra_height()/9.0)

func _local_cell_rect(x:float,y:float) -> Rect2:
	return Rect2(ORIGIN+Vector2(x,y)*_grid_step()+pan,_grid_step())

func _cell_rect(x:float,y:float) -> Rect2:
	var r:=_local_cell_rect(x,y)
	return Rect2(r.position+_restaurant_origin(),r.size)

func _room_y(y:float) -> float:
	if y<=ORIGIN.y: return y
	if y>=ORIGIN.y+CELL*9: return y+_extra_height()
	return ORIGIN.y+(y-ORIGIN.y)*(1.0+_extra_height()/(CELL*9))

func _set_draw_origin(origin:Vector2) -> void:
	drawing_offset=origin
	draw_set_transform(origin)

func _ready() -> void:
	branding = JSON.parse_string(FileAccess.get_file_as_string("res://branding.json"))
	balance = JSON.parse_string(FileAccess.get_file_as_string("res://balance.json"))
	audio = Audio.new()
	add_child(audio)
	if ResourceLoader.exists("res://assets/fonts/Body.ttf"):
		var body := FontVariation.new()
		body.base_font = load("res://assets/fonts/Body.ttf")
		body.variation_opentype = {2003265652:600.0}
		font = body
	if ResourceLoader.exists("res://assets/fonts/Display.ttf"): display = load("res://assets/fonts/Display.ttf")
	var saved := Save.read_save()
	if not saved.is_empty():
		model.restore(saved.restaurant)
		meta.merge(saved.get("meta", {}), true)
		restored_dive = saved.get("dive", {})
		result = saved.get("result", {})
		_offline(maxf(0, Time.get_unix_time_from_system() - float(saved.get("saved_at", Time.get_unix_time_from_system()))))
	audio.configure(meta.sound, meta.music)
	get_tree().auto_accept_quit = false
	set_process_input(true)

func _process(delta: float) -> void:
	if backgrounded: return
	clock += delta
	scene_time += delta
	toast_time = maxf(0, toast_time-delta)
	sale_ping = maxf(0, sale_ping-delta)
	board_shake = maxf(0,board_shake-delta)
	if screen == "loading":
		if load_progress < load_assets.size():
			var key: String = load_assets[load_progress]
			var p := "res://assets/v2/" + key + ".png"
			if not ResourceLoader.exists(p) and key.begins_with("customer_walk_"):
				p = "res://assets/v2/customer_4.png"
			if not ResourceLoader.exists(p): p = "res://assets/" + key + ".svg"
			if ResourceLoader.exists(p): textures[key] = load(p)
			load_progress += 1
		elif scene_time > 1.1:
			_change("title")
	elif screen == "intro" and scene_time > 9.5:
		_finish_intro()
	elif screen == "cutscene" and scene_time > 3.4:
		_change("reveal")
	if screen not in ["loading", "title", "intro"]:
		if not editing:
			var before: float = model.data.coins
			var events: Array = model.tick(minf(delta, 0.1))
			if is_instance_valid(dive):
				meta.pending_coins += model.data.coins-before
				model.data.coins = before
			for event in events:
				if event.get("type") == "sale" and screen == "restaurant":
					pops.append({"x":ORIGIN.x+float(event.get("x",3))*CELL+CELL/2,"y":ORIGIN.y+float(event.get("y",3))*_grid_step().y,"age":0.0})
					if sale_ping <= 0:
						audio.play("coin")
						sale_ping = 0.35
					if int(meta.tutorial) == 0: meta.tutorial = 1
		if not is_instance_valid(dive):
			meta.charge = minf(1, float(meta.charge)+delta/float(balance.charge_seconds))
	for p in pops: p.age += delta
	pops = pops.filter(func(p): return p.age < 1.2)
	autosave += delta
	if autosave > 3 and screen != "loading":
		autosave = 0
		_save()
	queue_redraw()

func _change(next: String) -> void:
	screen = next
	scene_time = 0
	moving = false
	pressed_action = ""
	drag_kind = ""
	modal = ""
	buttons.clear()
	audio.ambience("ocean" if next in ["dive","prep","cutscene","reveal","results"] else "restaurant")
	queue_redraw()

func _offline(seconds: float) -> void:
	if seconds < 3: return
	var before:float = model.data.coins
	var income: int = model.offline_income(seconds)
	if not restored_dive.is_empty() or is_instance_valid(dive):
		meta.pending_coins += income
		model.data.coins = before
	else:
		meta.charge = minf(1, float(meta.charge)+seconds/float(balance.charge_seconds))
	if income > 0: _notify("Welcome back! +%d coins from service" % income)

func _save() -> void:
	var dive_data: Dictionary = {}
	if is_instance_valid(dive): dive_data = dive.snapshot()
	elif not restored_dive.is_empty(): dive_data = restored_dive
	Save.write_save({"version":1,"saved_at":Time.get_unix_time_from_system(),"restaurant":model.serialize(),"meta":meta,"dive":dive_data,"result":result if screen in ["cutscene","reveal","results"] else {}})

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if not backgrounded and is_inside_tree() and audio != null:
			backgrounded = true
			moving = false
			pressed_action = ""
			drag_kind = ""
			audio.player.stream_paused = true
			background_stamp = Time.get_unix_time_from_system()
			if is_instance_valid(dive): dive.suspend()
			_save()
	elif what == NOTIFICATION_APPLICATION_RESUMED or what == NOTIFICATION_APPLICATION_FOCUS_IN:
		if backgrounded:
			backgrounded = false
			audio.player.stream_paused = false
			_offline(Time.get_unix_time_from_system()-background_stamp)
	elif what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_back()
	elif what == NOTIFICATION_WM_CLOSE_REQUEST:
		_save()
		get_tree().quit()

func _draw() -> void:
	buttons.clear()
	if screen == "dive": return
	_set_draw_origin(Vector2.ZERO)
	draw_rect(Rect2(Vector2.ZERO,size), PAPER)
	_set_draw_origin(_restaurant_origin() if screen=="restaurant" else _frame_origin())
	match screen:
		"loading": _loading()
		"title": _title()
		"intro": _intro()
		"restaurant": _restaurant()
		"shop": _shop()
		"workshop": _workshop()
		"prep": _prep()
		"cutscene": _cutscene()
		"reveal": _reveal()
		"results": _results()
	if modal != "":
		buttons.clear()
		_set_draw_origin(Vector2.ZERO)
		draw_rect(Rect2(Vector2.ZERO,size),Color(0.07,0.13,0.14,0.5))
		_set_draw_origin(_frame_origin())
		match modal:
			"settings": _settings()
			"chef": _chef_panel()
			"recipes": _recipes()
			"help": _help()
			"expand": _expand_panel()
			"reset": _reset_panel()
			"credits": _credits()
	if toast_time > 0 and screen not in ["loading","intro","cutscene"]:
		_set_draw_origin(_restaurant_origin())
		_panel(Rect2(50, 116, 620, 76), INK, 20)
		_center(toast, 360, 162, 23, PAPER)

func _panel(r: Rect2, color: Color=PAPER, radius: int=20, border: Color=INK, shadow: bool=false) -> void:
	if textures.has("paper_panel") and minf(r.size.x,r.size.y)>=35:
		var id:String="expedition_card" if r.size.y>r.size.x*0.55 and textures.has("expedition_card") else ("coral_panel" if color.is_equal_approx(CORAL) and textures.has("coral_panel") else "paper_panel")
		var tint:=Color.WHITE if id=="coral_panel" else Color(color.r/PAPER.r,color.g/PAPER.g,color.b/PAPER.b,color.a)
		if shadow: _nine_patch(textures[id],Rect2(r.position+Vector2(1,5),r.size),Color(0.17,0.12,0.08,0.26),radius)
		_nine_patch(textures[id],r,tint,radius)
		return
	if shadow:
		var sh := StyleBoxFlat.new()
		sh.bg_color=Color(0.1,0.16,0.14,0.17)
		sh.set_corner_radius_all(radius)
		draw_style_box(sh,Rect2(r.position+Vector2(0,5),r.size))
	var box:=StyleBoxFlat.new()
	box.bg_color=color; box.border_color=border
	box.set_border_width_all(3); box.set_corner_radius_all(radius)
	draw_style_box(box,r)

func _nine_patch(texture:Texture2D,r:Rect2,tint:Color,radius:int) -> void:
	var bounds:=Rect2(Vector2.ZERO,texture.get_size())
	if textures.has("expedition_card") and texture==textures.expedition_card: bounds=Rect2(10,212,1760,467)
	var source:=bounds.size
	var edge:=minf(112 if texture==textures.get("expedition_card") else 72,minf(source.x,source.y)/3)
	var dest_edge:=minf(float(radius)+12,minf(r.size.x,r.size.y)*0.30)
	var sx:=[0.0,edge,source.x-edge,source.x]
	var sy:=[0.0,edge,source.y-edge,source.y]
	var dx:=[r.position.x,r.position.x+dest_edge,r.end.x-dest_edge,r.end.x]
	var dy:=[r.position.y,r.position.y+dest_edge,r.end.y-dest_edge,r.end.y]
	for row in 3:
		for col in 3:
			var region:=Rect2(bounds.position+Vector2(sx[col],sy[row]),Vector2(sx[col+1]-sx[col],sy[row+1]-sy[row]))
			var destination:=Rect2(dx[col],dy[row],dx[col+1]-dx[col],dy[row+1]-dy[row])
			if destination.has_area(): draw_texture_rect_region(texture,destination,region,tint)

func _txt(s: String, p: Vector2, size_px: int=26, color: Color=INK, width: float=-1, fancy: bool=false) -> void:
	draw_string(display if fancy else font,p,s,HORIZONTAL_ALIGNMENT_LEFT,width,size_px,color)

func _center(s: String,x: float,y: float,size_px: int=26,color: Color=INK,fancy: bool=false) -> void:
	var f := display if fancy else font
	var w := f.get_string_size(s,HORIZONTAL_ALIGNMENT_LEFT,-1,size_px).x
	draw_string(f,Vector2(x-w/2,y),s,HORIZONTAL_ALIGNMENT_LEFT,-1,size_px,color)

func _paragraph(s: String, rect: Rect2, px: int=25, color: Color=INK, centered: bool=false) -> void:
	var y := rect.position.y+px
	for paragraph in s.split("\n"):
		var line := ""
		for word in paragraph.split(" "):
			if font.get_string_size(line+word,HORIZONTAL_ALIGNMENT_LEFT,-1,px).x > rect.size.x and line != "":
				if centered: _center(line.strip_edges(),rect.get_center().x,y,px,color)
				else: _txt(line.strip_edges(),Vector2(rect.position.x,y),px,color)
				y += px*1.4
				line = ""
			line += word+" "
		if centered: _center(line.strip_edges(),rect.get_center().x,y,px,color)
		else: _txt(line.strip_edges(),Vector2(rect.position.x,y),px,color)
		y += px*1.4

func _sprite(id: String, rect: Rect2, alpha: float=1.0) -> void:
	if textures.has(id):
		var texture:Texture2D=textures[id]
		var factor:float=minf(rect.size.x/texture.get_width(),rect.size.y/texture.get_height())
		var fitted:Vector2=texture.get_size()*factor
		draw_texture_rect(texture,Rect2(rect.get_center()-fitted/2,fitted),false,Color(1,1,1,alpha))

func _button(r: Rect2,label: String,action: String,data: Variant=null,color: Color=MINT,enabled: bool=true,px: int=26) -> void:
	var fill := color if enabled else Color("c9c7b9")
	_panel(r,fill,18,INK,true)
	_center(label,r.get_center().x,r.get_center().y+px*0.34,px,INK)
	if enabled: buttons.append({"rect":Rect2(r.position+drawing_offset,r.size),"action":action,"data":data})

func _hotspot(r: Rect2,action: String,data: Variant=null) -> void:
	buttons.append({"rect":Rect2(r.position+drawing_offset,r.size),"action":action,"data":data})

func _header(title: String, sub: String="") -> void:
	_center(title,360,80,42,INK,true)
	if sub != "": _center(sub,360,120,23,INK)

func _balance(salvage: bool=false) -> void:
	_panel(Rect2(30,35,225,68), PAPER,22,INK,true)
	if salvage: _sprite("gear",Rect2(46,44,49,49))
	else:
		draw_circle(Vector2(70,70),23,GOLD)
		draw_arc(Vector2(70,70),23,0,TAU,28,INK,3,true)
		_center("¢",70,80,30,INK)
	_txt(str(int(meta.salvage if salvage else model.data.coins)),Vector2(108,81),32)

func _loading() -> void:
	for y in range(0,1280,40): draw_line(Vector2(0,y),Vector2(720,y+8),Color("eddfc6"),1)
	_sprite("submarine",Rect2(275,350,170,220))
	_center("Warming the kitchen…",360,630,34,INK,true)
	_panel(Rect2(130,690,460,22),Color("e1d4bb"),11)
	var progress := float(load_progress)/load_assets.size()
	if progress > 0: _panel(Rect2(134,694,452*progress,14),CORAL,7,CORAL)
	_center("Gathering a little ocean of possibilities",360,778,21)

func _ocean_back(light: bool=false) -> void:
	var previous_origin:=drawing_offset
	_set_draw_origin(Vector2.ZERO)
	if textures.has("ocean_environment"):
		draw_texture_rect(textures.ocean_environment,Rect2(Vector2.ZERO,size),false,Color(0.84,0.97,1.0) if light else Color(0.64,0.76,0.82))
	else: draw_rect(Rect2(Vector2.ZERO,size),NAVY)
	for i in 30:
		var x := fmod(i*137.4,size.x)
		var y := fmod(i*99.7+clock*(8+i%3),size.y+40)-20
		draw_arc(Vector2(x,y),3+i%5,0,TAU,18,Color(0.45,0.77,0.78,0.24),2,true)
	_set_draw_origin(previous_origin)
func _title() -> void:
	_ocean_back(true)
	_panel(Rect2(58,112,604,964),PAPER,40,INK,true)
	_center("NIGHT SERVICE  /  DAY ADVENTURE",360,172,20)
	_center(branding.title,360,260,68,INK,true)
	_center(branding.tagline,360,306,27)
	_sprite("title_vignette",Rect2(107,346,506,432))
	if not textures.has("title_vignette"):
		_sprite("chef",Rect2(166,390,200,230))
		_sprite("submarine",Rect2(381,534,134,199))
	_center("Cook. Discover. Make room for more.",360,819,23)
	_button(Rect2(132,863,456,82),"Resume voyage" if not restored_dive.is_empty() else "Open the shutters", "play",null,CORAL, true,30)
	_button(Rect2(132,968,216,62),"Settings","settings",null,PAPER, true,24)
	_button(Rect2(371,968,216,62),"How to play","help",null,PAPER,true,24)
	_center(branding.edition+"  •  "+branding.version,360,1185+_extra_height()/2,20,PAPER)

func _intro() -> void:
	var step := mini(2,int(scene_time/3.15))
	_ocean_back(step==0)
	var titles := ["A tiny place, all yours.","Good food brings us together.","The next recipe is out there."]
	var copy := ["On a quiet harbor, one little kitchen lights up the night.","The belt keeps turning. The guests keep coming. Your crew makes it home.","By day, take your submarine into the blue. Bring a little wonder back for dinner."]
	_panel(Rect2(60,142,600,890),PAPER,32,INK,true)
	_center(titles[step],360,235,38,INK,true)
	var bob := 0.0 if meta.reduced_motion else sin(clock*2)*9
	if step==0:
		_sprite("chef",Rect2(230,338+bob,260,280))
		_sprite("lantern",Rect2(90,290,95,170))
	elif step==1:
		_sprite("customer_1",Rect2(130,360,210,240))
		_sprite("customer_3",Rect2(380,370,200,230))
		_sprite("salmon",Rect2(285,530+bob,150,120))
	else:
		_sprite("submarine",Rect2(270,330+bob,180,300))
		_sprite("creature_salmon",Rect2(455,365,120,135))
	_paragraph(copy[step],Rect2(113,725,494,150),28,INK,true)
	for i in 3: draw_circle(Vector2(330+i*30,940),6,CORAL if i==step else Color("cfc4aa"))
	_button(Rect2(215,1100,290,65),"Enter the harbor","finish_intro",null,PAPER, true,25)

func _finish_intro() -> void:
	meta.intro_seen = true
	_change("restaurant")
	_save()

func _restaurant() -> void:
	_set_draw_origin(Vector2.ZERO)
	if textures.has("restaurant_environment"):
		var texture:Texture2D=textures.restaurant_environment
		var source:=texture.get_size()
		var bands:=[0.0,ORIGIN.y,ORIGIN.y+CELL*9,1280.0]
		for band in 3:
			var start:float=bands[band]
			var finish:float=bands[band+1]
			var region:=Rect2(0,start/1280*source.y,source.x,(finish-start)/1280*source.y)
			draw_texture_rect_region(texture,Rect2(0,_room_y(start),size.x,_room_y(finish)-_room_y(start)),region)
	else: draw_rect(Rect2(Vector2.ZERO,size),PAPER)
	_set_draw_origin(_restaurant_origin())
	# A restrained living light belongs to the lanterns in the painted scene.
	if not meta.reduced_motion:
		for at in [Vector2(215,67),Vector2(490,67)]:
			draw_circle(at,48,Color(1.0,0.72,0.27,0.035+0.012*sin(clock*1.8)))
	_balance()
	_button(Rect2(551,26,63,63),"?","help",null,PAPER,true,31)
	_button(Rect2(632,26,63,63),"☰","settings",null,PAPER,true,30)
	if editing:
		_panel(Rect2(276,35,223,49),PAPER,14)
		_center("LAYOUT PAUSED",387,66,20)
	# Entrances are actual parts of the illustration; names stay in live UI.
	_panel(Rect2(36,173,120,36),PAPER,7)
	_center("Shop",96,198,20,INK,true)
	_panel(Rect2(559,174,133,36),PAPER,7)
	_center("Workshop",625,198,18,INK,true)
	_hotspot(Rect2(13,105,161,141),"shop")
	_hotspot(Rect2(549,97,165,153),"workshop")
	# The painted perimeter carries the clutter; a few uneven piles mark expansion.
	for y in 9:
		for x in 8:
			var r:=_local_cell_rect(x,y)
			if model.is_floor(x,y) and int(meta.floor_style)==1:
				draw_rect(r,Color(0.34,0.66,0.59,0.2 if (x+y)%2==0 else 0.12))
	if not model.data.expanded:
		for pile in [{"at":Vector2(92,467),"size":Vector2(107,99),"angle":-0.04,"flip":false},{"at":Vector2(702,748),"size":Vector2(100,100),"angle":0.035,"flip":true},{"at":Vector2(139,965),"size":Vector2(167,110),"angle":0.015,"flip":false}]:
			draw_set_transform(Vector2(pile.at.x,_room_y(pile.at.y))+pan+drawing_offset,pile.angle,Vector2(-1,1) if pile.flip else Vector2.ONE)
			_sprite("rubble_cluster",Rect2(-pile.size/2,pile.size))
			draw_set_transform(drawing_offset)
	# Continuous ribbon, then dishes, then all people sorted by their feet.
	var objects:Array=model.data.objects
	_draw_belt_ribbon(objects)
	for o in objects:
		if o.kind=="belt": _draw_object(o)
	var actors:Array=[]
	for o in objects:
		if o.kind!="belt": actors.append({"object":o,"y":float(o.y)})
	for c in model.data.get("customers",[]):
		if c.get("state","") not in ["seated","eating"]: actors.append({"person":c,"y":float(c.y)})
	actors.sort_custom(func(a,b):return float(a.y)<float(b.y))
	for actor in actors:
		if actor.has("object"): _draw_object(actor.object)
		else:
			var c:Dictionary=actor.person
			var foot:=_local_cell_rect(float(c.x),float(c.y)).get_center()+Vector2(0,29)
			var stride:=sin(clock*9+int(c.id))*2.8 if not editing and not meta.reduced_motion else 0.0
			draw_ellipse_shadow(foot+Vector2(0,-3),Vector2(24,7))
			_foot_sprite("customer_walk_"+str(1+int(c.id)%3),foot+Vector2(0,stride),124,90)
	if editing:
		for y in 9:
			for x in 8:
				var cell_rect:=_local_cell_rect(x,y)
				if model.is_floor(x,y): draw_rect(cell_rect,Color(0.18,0.3,0.29,0.17),false,1)
				else:
					draw_rect(cell_rect,Color(0.14,0.18,0.14,0.2))
					draw_line(cell_rect.position+Vector2(12,12),cell_rect.end-Vector2(12,12),Color(0.2,0.2,0.18,0.2),1,true)
		if last_path>=0:
			var o:Dictionary=model.get_object(last_path)
			if not o.is_empty():
				for dir in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
					var cell:Vector2i=Vector2i(int(o.x),int(o.y))+dir
					if model.is_floor(cell.x,cell.y): draw_rect(_local_cell_rect(cell.x,cell.y).grow(-3),Color(0.28,0.61,0.51,0.18+0.1*sin(clock*3)))
		var chosen:Dictionary=model.get_object(selected)
		if not chosen.is_empty(): draw_rect(_local_cell_rect(chosen.x,chosen.y).grow(-2),Color("277d7c"),false,4)
	for p in pops:
		var pos:=Vector2(p.x,p.y-p.age*43)+pan
		draw_circle(pos,11,GOLD)
		draw_arc(pos,11,0,TAU,24,INK,2,true)
		_center("¢",pos.x,pos.y+6,16)
	# Dock and construction controls remain anchored to the actual lower edge.
	_set_draw_origin(_restaurant_origin()+Vector2(0,_extra_height()))
	var dock_bob:=sin(clock*1.6)*3 if not meta.reduced_motion else 0.0
	var glow:=0.09+0.04*sin(clock*2) if float(meta.charge)>=1 else 0.025
	draw_colored_polygon(PackedVector2Array([Vector2(558,1098),Vector2(506,1038),Vector2(616,1038)]),Color(1,0.87,0.48,glow))
	_sprite("submarine",Rect2(501,1062+dock_bob,122,168))
	_panel(Rect2(433,1121,70,29),PAPER,6)
	if float(meta.charge)>0: draw_rect(Rect2(439,1127,58*float(meta.charge),17),MINT)
	_hotspot(Rect2(411,1057,247,181),"dock")
	var hint:String="Tap a chef to choose a recipe."
	if int(meta.tutorial)==0: hint="Your chef is cooking. Watch the first guest."
	elif int(meta.tutorial)==1: hint="First sale! Tap your chef to grow the menu."
	elif int(meta.tutorial)==2: hint="The submarine is charged. Tap it to explore."
	if editing: hint="Drag from the tray. Select, then move or rotate."
	if int(meta.tutorial)<3 or editing:
		_panel(Rect2(125,1004,474,47),PAPER,13)
		_center(hint,362,1035,19)
	if not editing:
		_tool_icon(Rect2(50,1166,76,79),"edit","hammer")
		_tool_icon(Rect2(143,1166,76,79),"crew","chef")
		_tool_icon(Rect2(236,1166,76,79),"shop","seat")
	else:
		_panel(Rect2(15,1133,690,131),PAPER,24)
		if selected>=0 or last_path>=0:
			_button(Rect2(31,1161,125,72),"Rotate","rotate",null,GOLD,true,22)
			_button(Rect2(170,1161,125,72),"Store","store",null,PAPER,true,22)
			_button(Rect2(308,1161,67,72),"×","deselect",null,PAPER,true,32)
		else:
			_tool_icon(Rect2(28,1160,68,77),"layer","layout",1,MINT if layer==1 else PAPER)
			_tool_icon(Rect2(106,1160,68,77),"layer","chef",0,MINT if layer==0 else PAPER)
			_tool_icon(Rect2(184,1160,68,77),"layer","floor",2,MINT if layer==2 else PAPER)
			if layer==2: _button(Rect2(267,1160,150,77),"Floor","floor",null,GOLD,true,22)
			else:
				var kind:String="chef" if layer==0 else "belt"
				_button(Rect2(267,1160,94,77),"%s %d" % ["Crew" if kind=="chef" else "Belt",int(model.data.inventory.get(kind,0))],"inventory",kind,PAPER,true,17)
				if layer==1: _button(Rect2(369,1160,93,77),"Seat %d" % int(model.data.inventory.get("seat",0)),"inventory","seat",PAPER,true,17)
		_button(Rect2(479,1160,203,77),"Live ›","live",null,CORAL,true,27)
	if drag_kind!="":
		_set_draw_origin(Vector2.ZERO)
		_sprite("chef" if drag_kind=="chef" else "seat",Rect2(pointer_last-Vector2(42,64),Vector2(84,128)),0.8)

func _tool_icon(r:Rect2,action:String,icon:String,data:Variant=null,color:Color=PAPER) -> void:
	_panel(r,color,16,INK,true)
	if icon in ["chef","seat"]:
		_sprite(icon,r.grow(-10))
	elif icon=="hammer":
		var c:=r.get_center()
		draw_line(c+Vector2(-16,20),c+Vector2(8,-8),Color("8a6042"),12,true)
		draw_line(c+Vector2(-16,20),c+Vector2(8,-8),INK,2,true)
		draw_colored_polygon(PackedVector2Array([c+Vector2(-9,-22),c+Vector2(17,-3),c+Vector2(27,-17),c+Vector2(0,-35)]),Color("a1aaa9"))
		draw_polyline(PackedVector2Array([c+Vector2(-9,-22),c+Vector2(17,-3),c+Vector2(27,-17),c+Vector2(0,-35),c+Vector2(-9,-22)]),INK,3,true)
	else:
		var c:=r.get_center()
		for row in 2:
			for col in 2: _panel(Rect2(c+Vector2(-19+col*20,-19+row*20),Vector2(17,17)),CORAL if icon=="layout" else MINT,3)
	_hotspot(r,action,data)

func _foot_sprite(id:String,foot:Vector2,height:float,width:float) -> void:
	if not textures.has(id): return
	var texture:Texture2D=textures[id]
	var ratio:float=minf(height/texture.get_height(),width/texture.get_width())
	var size_v:=texture.get_size()*ratio
	draw_texture_rect(texture,Rect2(foot-Vector2(size_v.x/2,size_v.y),size_v),false)

func _draw_belt_ribbon(objects:Array) -> void:
	var segments:Array=[]
	for o in objects:
		if o.kind!="belt": continue
		var center:=_local_cell_rect(float(o.x),float(o.y)).get_center()
		var end:=center
		var next:Dictionary=model.object_at(model.facing_cell(o).x,model.facing_cell(o).y)
		if next.get("kind")=="belt": end=_local_cell_rect(float(next.x),float(next.y)).get_center()
		segments.append([center,end])
	for segment in segments:
		draw_line(segment[0]+Vector2(4,11),segment[1]+Vector2(4,11),Color(0.20,0.15,0.10,0.22),75,true)
		draw_circle(segment[0]+Vector2(4,11),37.5,Color(0.20,0.15,0.10,0.22))
	for width in [77,71,65,49]:
		var color:Color={77:Color("262629"),71:Color("eae1c9"),65:Color("c95d4c"),49:Color("56575a")}[width]
		for segment in segments:
			draw_line(segment[0],segment[1],color,width,true)
			draw_circle(segment[0],float(width)/2,color)
			draw_circle(segment[1],float(width)/2,color)
	if textures.has("belt_material"):
		for segment in segments:
			var start:Vector2=segment[0]
			var end:Vector2=segment[1]
			if start.distance_to(end)>1:
				var side:Vector2=start.direction_to(end).orthogonal()*24.5
				_belt_material_polygon(PackedVector2Array([start+side,end+side,end-side,start-side]))
			for at in [start,end]:
				var circle:=PackedVector2Array()
				for i in 32: circle.append(at+Vector2.from_angle(i*TAU/32)*24.5)
				_belt_material_polygon(circle)

func _belt_material_polygon(points:PackedVector2Array) -> void:
	var uv:=PackedVector2Array()
	for point in points: uv.append((point-pan)/Vector2(720,1280+_extra_height()))
	draw_polygon(points,PackedColorArray([Color.WHITE]),uv,textures.belt_material)

func _draw_object(o:Dictionary) -> void:
	var r:=_local_cell_rect(float(o.x),float(o.y))
	var center:=r.get_center()
	match str(o.kind):
		"belt":
			var dir:int=int(o.get("dir",0))
			var v:=Vector2.UP.rotated(dir*PI/2) if dir>=0 else Vector2.ZERO
			var sideways:=v.rotated(PI/2)
			var belt_time:float=float(model.data.time)
			for i in 3:
				var offset:=fmod(belt_time*20,27)+i*27-40
				var at:=center+v*offset
				draw_polyline(PackedVector2Array([at-sideways*21-v*4,at-v*1.5,at+sideways*21-v*4]),Color(0.83,0.76,0.61,0.23),1.4,true)
				for n in 3: draw_line(at+sideways*(-16+n*14)+v*7,at+sideways*(-10+n*14)+v*8,Color(1,0.94,0.76,0.05),1,true)
			if o.get("dish","")!="":
				draw_ellipse_shadow(center+Vector2(2,9),Vector2(26,8))
				_sprite(str(o.dish),Rect2(center-Vector2(33,28),Vector2(66,56)))
		"chef":
			var bob:float=sin(clock*4+int(o.id))*1.5 if not editing and not meta.reduced_motion else 0.0
			var foot:=center+Vector2(0,30)
			draw_ellipse_shadow(foot+Vector2(0,-4),Vector2(25,8))
			_foot_sprite("chef" if int(o.id)%2==0 else "chef_2",foot+Vector2(0,bob),139,99)
			var shake:float=sin(clock*42)*3 if int(o.id)==selected and board_shake>0 and not meta.reduced_motion else 0.0
			var board:=Rect2(center+Vector2(-42+shake,0),Vector2(41,58))
			_sprite("blackboard",board)
			_sprite(str(o.get("recipe","cucumber")),Rect2(board.position+Vector2(5,9),Vector2(31,26)))
		"seat":
			var foot:=center+Vector2(0,33)
			draw_ellipse_shadow(foot+Vector2(3,-3),Vector2(30,8))
			_foot_sprite("seat",foot,105,87)
			var c:Dictionary=o.get("customer",{})
			if not c.is_empty():
				var happy:float=float(c.get("happy_time",0))
				var bounce:float=sin(clock*(8 if happy>0 else 3))* (4.0 if happy>0 else 1.2) if not editing and not meta.reduced_motion else 0.0
				var id:String="customer_"+str(1+int(c.get("id",o.id))%3)
				_foot_sprite(id,foot+Vector2(0,-5+bounce),132,95)
				var bubble:=center+Vector2(41,-86)
				if happy>0:
					_panel(Rect2(bubble-Vector2(23,22),Vector2(46,44)),PAPER,20)
					_center("♥",bubble.x,bubble.y+8,25,CORAL)
				elif c.get("wish","")!="" and float(c.get("eaten",0))==0 and float(c.get("preference_time",0))>0:
					_panel(Rect2(bubble-Vector2(27,24),Vector2(54,49)),PAPER,21)
					_sprite(str(c.wish),Rect2(bubble-Vector2(20,18),Vector2(40,36)))
					var fraction:float=float(c.get("preference_time",0))/maxf(1,float(c.get("preference_total",8)))
					draw_arc(bubble,29,-PI/2,-PI/2+fraction*TAU,24,CORAL,2,true)
		"plant": _sprite("plant",r.grow(-3))
	if editing and int(o.get("dir",-1))>=0:
		var direction:=Vector2.UP.rotated(int(o.dir)*PI/2)
		var side:=direction.rotated(PI/2)
		var tip:=center+direction*32
		var pts:=PackedVector2Array([tip,tip-direction*12+side*7,tip-direction*12-side*7])
		draw_colored_polygon(pts,PAPER)
		draw_polyline(PackedVector2Array([pts[0],pts[1],pts[2],pts[0]]),INK,2,true)

func draw_ellipse_shadow(pos: Vector2, scale_v: Vector2) -> void:
	var pts:=PackedVector2Array()
	for i in 24: pts.append(pos+Vector2(cos(i*TAU/24),sin(i*TAU/24))*scale_v)
	draw_colored_polygon(pts,Color(0.16,0.21,0.17,0.16))

func _chef_panel() -> void:
	var c:Dictionary=model.get_object(selected)
	if c.is_empty(): return
	_panel(Rect2(65,250,590,778),PAPER,30,INK,true)
	_button(Rect2(565,273,60,60),"×","close",null,PAPER,true,35)
	_sprite("chef",Rect2(116,316,160,182))
	_txt("YOUR KITCHEN CREW",Vector2(306,350),20)
	_txt("Chef %s" % c.get("name","Miso"),Vector2(306,401),32,INK,-1,true)
	_txt("Level %d" % int(c.level),Vector2(306,446),28)
	var prep:float=model.chef_prep_time(c,str(c.recipe))
	_paragraph("Preparing %s\n%.1f seconds per dish" % [balance.recipes.get(c.recipe,{}).get("name",c.recipe),prep],Rect2(115,528,490,110),26)
	_button(Rect2(115,653,490,77),"Choose recipe","recipes",null,MINT)
	var cost: int=model.upgrade_cost(selected)
	var cap: int=int(c.get("max_level",12))
	var level: int=int(c.level)
	_paragraph("Faster cooking with every level. Steel at 3 · Copper at 5.",Rect2(115,770,490,80),22)
	_button(Rect2(115,885,490,77),"MAX" if level>=cap else "Level up  ·  %d coins" % cost,"chef_upgrade",null,GOLD,level<cap and model.data.coins>=cost)

func _recipes() -> void:
	var chef: Dictionary=model.get_object(selected)
	if chef.is_empty(): return
	_panel(Rect2(30,132,660,1075),PAPER,26,INK,true)
	_center("The recipe book",340,205,38,INK,true)
	_button(Rect2(596,158,62,62),"×","close",null,PAPER,true,35)
	var names: Array=balance.recipes.keys()
	names.sort_custom(func(a,b):
		var ra:Dictionary=balance.recipes[a]; var rb:Dictionary=balance.recipes[b]
		var ga:int=0 if a in model.data.recipes and int(ra.level)<=int(chef.level) else (1 if a in model.data.recipes else 2)
		var gb:int=0 if b in model.data.recipes and int(rb.level)<=int(chef.level) else (1 if b in model.data.recipes else 2)
		return int(ra.tier)>int(rb.tier) if ga==gb else ga<gb)
	for i in names.size():
		var id:String=names[i]; var r:Dictionary=balance.recipes[id]
		var known:bool=id in model.data.recipes
		var rect:=Rect2(62+(i%2)*310,252+int(i/2)*230,286,209)
		var colors: Array=[Color("d2aa74"),Color("b8c5c4"),Color("c98e65"),Color("cdd5dc"),GOLD]
		_panel(rect,colors[int(r.tier)],15,Color("796347"))
		for n in 4: draw_line(rect.position+Vector2(15,25+n*39),rect.position+Vector2(271,21+n*39),Color(0.15,0.18,0.16,0.1),2,true)
		if known: _sprite(id,Rect2(rect.position+Vector2(75,9),Vector2(135,108)))
		else:
			draw_circle(rect.position+Vector2(143,70),42,Color(0.2,0.23,0.2,0.17))
			_center("?",rect.position.x+143,rect.position.y+91,54,Color("786a55"),true)
		_center(str(r.name) if known else "Undiscovered",rect.get_center().x,rect.position.y+151,25)
		_center(TIERS[int(r.tier)],rect.get_center().x,rect.position.y+184,19)
		if id==str(chef.recipe):
			draw_circle(rect.position+Vector2(24,25),7,CORAL)
			draw_arc(rect.position+Vector2(24,25),7,0,TAU,18,INK,1.5,true)
		if id==selected_recipe:
			var selected_border:=StyleBoxFlat.new()
			selected_border.bg_color=Color.TRANSPARENT
			selected_border.border_color=Color("2b7779")
			selected_border.set_border_width_all(3)
			selected_border.set_corner_radius_all(17)
			draw_style_box(selected_border,rect.grow(2))
		if id in meta.new_recipes:
			_panel(Rect2(rect.position+Vector2(181,10),Vector2(87,31)),CORAL,7)
			_center("NEW",rect.position.x+224,rect.position.y+33,18)
		if known: _hotspot(rect,"inspect_recipe",id)
	var r:Dictionary=balance.recipes[selected_recipe]
	var eligible: bool=int(chef.level)>=int(r.level)
	_panel(Rect2(60,764,600,405),Color("f4e5c5"),20)
	_sprite(selected_recipe,Rect2(82,790,156,131))
	_txt(str(r.name),Vector2(258,824),32,INK,-1,true)
	_txt("%d coins / dish" % int(r.price),Vector2(258,868),25)
	_txt(("%.1f sec / dish" % model.chef_prep_time(chef,selected_recipe)) if eligible else "— sec / dish",Vector2(258,908),24)
	_center("Requires %s chef · Level %d" % [TIERS[int(r.tier)],int(r.level)],360,973,24)
	var current: bool=selected_recipe==str(chef.recipe)
	_button(Rect2(95,1030,530,85),"Preparing" if current else ("Prepare" if eligible else "Chef level %d needed" % int(r.level)),"prepare",null,MINT,eligible and not current)

func _shop() -> void:
	_center("The corner shop",477,82,38,INK,true)
	_balance()
	# Balance is lifted below the heading on this screen.
	_panel(Rect2(37,162,646,112),Color("e4bc8b"),20)
	_sprite("plant",Rect2(53,175,81,86))
	_paragraph("Everything you buy goes into your tray. Arrange the room to place it.",Rect2(157,181,492,78),23)
	var goods := [{"kind":"belt","label":"Belt tile","copy":"Make a path. Close a loop.","icon":"cucumber"},{"kind":"seat","label":"Customer seat","copy":"A little room for one more.","icon":"customer_1"},{"kind":"chef","label":"Hire Chef Nori","copy":"Growth 13% / level · max 12 · Gold","icon":"chef"}]
	for i in goods.size():
		var g:Dictionary=goods[i]; var y:=310+i*226
		_panel(Rect2(43,y,634,201),PAPER,24,INK,true)
		_sprite(g.icon,Rect2(61,y+28,132,141))
		_txt(g.label,Vector2(215,y+49),31,INK,-1,true)
		_txt(g.copy,Vector2(215,y+84),18)
		var price:int=model.price_for(g.kind)
		_button(Rect2(214,y+112,417,62),"%d coins  ·  Buy" % price,"buy",g.kind,GOLD,model.data.coins>=price,24)
	var owned:bool=meta.get("mint_floor_owned",false)
	_panel(Rect2(43,1005,634,112),Color("c4d6c9"),20)
	_txt("Sea-glass floor",Vector2(77,1058),27,INK,-1,true)
	_button(Rect2(377,1026,270,67),"Owned" if owned else "120 coins · Buy","buy_floor",null,PAPER,not owned and model.data.coins>=120,23)
	_door_back()

func _door_back() -> void:
	var previous_origin:=drawing_offset
	_set_draw_origin(_restaurant_origin()+Vector2(0,_extra_height()))
	_button(Rect2(225,1170,270,75),"Sushi Bar  ›","restaurant",null,CORAL,true,27)
	_set_draw_origin(previous_origin)

func _workshop() -> void:
	_header("The workshop","A little stronger with every voyage.")
	_panel(Rect2(234,146,252,72),PAPER,22)
	_sprite("gear",Rect2(250,157,50,50))
	_center("%d salvage" % int(meta.salvage),382,192,25)
	_sprite("submarine",Rect2(275,235+sin(clock*1.8)*5,170,230))
	for i in 3:
		var key:String=["hull","harpoon","collector"][i]
		var cfg:Dictionary=balance.equipment[key]
		var lvl:int=int(meta.upgrades[key]); var maximum:bool=lvl>=int(cfg.cap)
		var cost:int=int(cfg.cost)*(lvl+1)
		var stat:float=float(cfg.base)+float(cfg.gain)*lvl
		var y:=505+i*198
		_panel(Rect2(47,y,626,177),PAPER,23,INK,true)
		_txt(cfg.name,Vector2(83,y+51),31,INK,-1,true)
		_txt("Level %d / %d" % [lvl,int(cfg.cap)],Vector2(75,y+80),21)
		var preview:=str(stat).trim_suffix(".0")+("" if maximum else "  →  "+str(stat+float(cfg.gain)).trim_suffix(".0"))
		_txt(preview+" "+str(cfg.unit),Vector2(74,y+128),23)
		_button(Rect2(405,y+28,239,74),"MAX" if maximum else "Upgrade · %d" % cost,"equipment",key,GOLD,not maximum and int(meta.salvage)>=cost,22)
	_door_back()

func _prep() -> void:
	_ocean_back(true)
	_center("Choose your waters",360,105,43,PAPER,true)
	_center("Three hand-drawn expedition charts",360,150,24,PAPER)
	for i in 3:
		var route:Dictionary=balance.routes[i]
		var y:=207+i*172
		_panel(Rect2(53,y,614,147),Color(route.color),23,INK,true)
		if selected_route==i: draw_rect(Rect2(60,y+7,600,133),PAPER,false,3)
		_center("0%d" % (i+1),110,y+85,37,INK,true)
		_txt(route.name,Vector2(164,y+56),32,INK,-1,true)
		_txt(route.subtitle,Vector2(164,y+94),22)
		if i in meta.completed: _txt("Charted",Vector2(530,y+124),19)
		_hotspot(Rect2(53,y,614,147),"route",i)
	_sprite("submarine",Rect2(272,752+sin(clock*2)*5,176,238))
	_button(Rect2(136,1010,448,84),"Start expedition","launch",null,GOLD,true,30)
	_door_back()

func _cutscene() -> void:
	_ocean_back(true)
	var phase:=clampf(scene_time/3.4,0,1)
	var ray_alpha:=sin(phase*PI)*0.18
	for i in 10:
		var angle:=i*TAU/10+clock*0.15
		var pts:=PackedVector2Array([Vector2(360,540),Vector2(360,540)+Vector2.from_angle(angle)*900,Vector2(360,540)+Vector2.from_angle(angle+0.18)*900])
		draw_colored_polygon(pts,Color(1,0.87,0.54,ray_alpha))
	var species:String=result.get("species","salmon")
	var creature_y:=460-sin(phase*PI)*80
	_sprite("creature_"+species,Rect2(222,creature_y,276,246),1-clampf((phase-0.6)*2.5,0,1))
	_sprite(species,Rect2(237,419,246,214),clampf((phase-0.4)*2.5,0,1))
	_sprite("submarine",Rect2(288,790-phase*35,144,207))
	_center("A little discovery…",360,230,43,PAPER,true)
	_center("…a whole new possibility.",360,1100,30,PAPER,true)
	for i in 20:
		var angle:=i*2.4
		var rad:=90+phase*260
		var p:=Vector2(360,540)+Vector2.from_angle(angle)*rad
		draw_circle(p,3+i%4,Color(1,0.85,0.45,0.8*(1-phase)))

func _reveal() -> void:
	_ocean_back(true)
	var species:String=result.get("species","salmon")
	var recipe:Dictionary=balance.recipes[species]
	_panel(Rect2(62,199,596,899),PAPER,30,INK,true)
	_center("A NEW RECIPE",360,272,23,INK)
	_center(recipe.name,360,339,44,INK,true)
	_panel(Rect2(148,393,424,299),[Color("d2aa74"),Color("b8c5c4"),Color("c98e65")][int(recipe.tier)],25)
	_sprite(species,Rect2(220,430+sin(clock*2)*5,280,210))
	_center("%d coins per dish" % int(recipe.price),360,755,31)
	_center("%.1f seconds · base preparation" % float(recipe.prep),360,809,25)
	_center("Requires a %s chef · Level %d" % [TIERS[int(recipe.tier)],int(recipe.level)],360,863,25)
	_paragraph("Your discovery is saved. Choose Prepare in a chef's recipe book to put it on the belt.",Rect2(110,910,500,86),22,INK,true)
	_button(Rect2(164,1003,392,70),"Continue","results",null,CORAL,true,29)

func _results() -> void:
	_ocean_back(result.get("outcome")=="complete")
	var outcome:String=result.get("outcome","early")
	if ResourceLoader.exists("res://assets/v2/results_"+outcome+".png"):
		_sprite("results_"+outcome,Rect2(152,305,416,166))
	else: _sprite("submarine",Rect2(303,308,114,164))
	var title:String={"complete":"Expedition complete","early":"Returned early","failed":"Hull depleted"}.get(outcome,"Expedition complete")
	_panel(Rect2(48,128,624,104),NAVY,22)
	_center(title,360,193,41,PAPER,true)
	_panel(Rect2(84,250,552,55),PAPER,20)
	_center("Every little find comes home with you.",360,286,23,INK)
	_panel(Rect2(75,475,570,560),PAPER,27,INK,true)
	_center("THE SALVAGE RECEIPT",360,539,25)
	var entries := [["Recovered",int(result.get("pickups",0))],["Familiar catch",int(result.get("repeat_bonus",0))],["Route complete",int(result.get("completion_bonus",0))]]
	for i in entries.size():
		_txt(str(entries[i][0]),Vector2(115,605+i*67),27)
		_txt(str(entries[i][1]),Vector2(540,605+i*67),29)
	draw_dashed_line(Vector2(113,779),Vector2(607,779),Color("a4987f"),2,8)
	_txt("TOTAL EARNED",Vector2(115,842),23)
	_txt(str(int(result.get("total",0))),Vector2(492,853),47,INK,-1,true)
	var explanation: String="A full battery awaits after night service."
	if outcome=="early": explanation="Early return: no completion bonus."
	elif outcome=="failed": explanation="Hull depleted: no completion bonus."
	_center(explanation,360,915,23)
	if not result.get("caught",false): _center("The creature is still out there.",360,959,24)
	_button(Rect2(152,1093,416,88),"Restaurant","results_home",null,CORAL,true,31)

func _settings() -> void:
	_panel(Rect2(70,235,580,815),PAPER,30,INK,true)
	_center("A moment of quiet",330,305,37,INK,true)
	_button(Rect2(558,257,61,61),"×","close",null,PAPER,true,35)
	var items := [["music","Music"],["sound","Sound effects"],["haptics","Gentle vibrations"],["reduced_motion","Reduced motion"]]
	for i in items.size():
		var item:Array=items[i]
		_button(Rect2(114,359+i*110,492,80),str(item[1])+"  ·  "+("On" if meta[item[0]] else "Off"),"setting",item[0],MINT if meta[item[0]] else Color("e5dcc8"),true,26)
	_center("Made for small, unhurried adventures.",360,853,21)
	_button(Rect2(163,867,394,48),"Credits & licenses","credits",null,PAPER,true,21)
	_button(Rect2(114,940,492,65),"Start a fresh exhibition","reset_confirm",null,PAPER,true,23)

func _help() -> void:
	_panel(Rect2(45,156,630,987),PAPER,28,INK,true)
	_center("Your harbor handbook",335,222,38,INK,true)
	_button(Rect2(584,177,62,62),"×","close",null,PAPER,true,35)
	var sections := [["01  Let the kitchen cook","Chefs cook automatically. Guests walk to seats and take plates from the belt. Tap a chef to level up or choose a recipe."],["02  Make room for more","Shop for belts, seats and crew. Arrange pauses the room: drag from the tray, or select then move an object. Rotate it to face one belt tile. Live resumes service."],["03  Follow your curiosity","Tap the charged submarine, choose a chart, then Start. Drag sideways to steer. Collect gears; avoid rocks. Tap the harpoon when aligned, then follow the creature's glowing strip."],["04  Bring it home","New catches unlock recipes. Salvage upgrades your submarine in the Workshop. Coins grow your kitchen. Charge refills over 2½ minutes, even while away."]]
	for i in sections.size():
		_txt(sections[i][0],Vector2(89,289+i*197),28,INK,-1,true)
		_paragraph(sections[i][1],Rect2(89,310+i*197,544,130),23)
	_center("Progress saves automatically. Play offline.",360,1100,22)

func _expand_panel() -> void:
	_panel(Rect2(77,379,566,483),PAPER,25,INK,true)
	_center("A little more possibility",360,452,36,INK,true)
	_paragraph("Clear the crates around the kitchen to open more floor and room for a larger crew. Your existing layout stays put.",Rect2(124,493,472,151),27,INK,true)
	var cost:int=model.price_for("expand")
	_button(Rect2(120,682,480,74),"Clear  ·  %d coins" % cost,"expand",null,GOLD,model.data.coins>=cost)
	_button(Rect2(225,782,270,55),"Cancel","close",null,PAPER,true,24)

func _reset_panel() -> void:
	_panel(Rect2(76,397,568,447),PAPER,25,INK,true)
	_center("Start fresh?",360,472,41,INK,true)
	_paragraph("This resets this exhibition's kitchen, recipes, equipment and saved voyage on this device.",Rect2(128,513,464,140),27,INK,true)
	_button(Rect2(125,668,470,69),"Keep my harbor","settings",null,MINT,true,27)
	_button(Rect2(125,759,470,58),"Reset progress","reset",null,PAPER,true,23)

func _input(event: InputEvent) -> void:
	if screen in ["loading","cutscene"] or backgrounded: return
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
		_back(); return
	if screen=="dive": return
	if event is InputEventScreenTouch:
		if event.index!=0: return
		if event.canceled:
			moving=false; pressed_action=""; drag_kind=""; return
		var local_position:Vector2=get_global_transform_with_canvas().affine_inverse()*event.position
		if event.pressed: _pointer_down(local_position)
		else: _pointer_up(local_position)
	elif event is InputEventScreenDrag and event.index==0:
		_pointer_move(get_global_transform_with_canvas().affine_inverse()*event.position)

func _pointer_down(pos: Vector2) -> void:
	pointer_start=pos; pointer_last=pos; moving=true; dragged=false
	pressed_action=""; pressed_data=null; drag_kind=""
	for i in range(buttons.size()-1,-1,-1):
		var b:Dictionary=buttons[i]
		if b.rect.has_point(pos):
			pressed_action=b.action; pressed_data=b.data
			if pressed_action=="inventory":
				drag_kind=str(b.data)
			return
	if screen=="restaurant" and modal=="" and editing and selected>=0:
		var c:=_cell(pos)
		var o:Dictionary=model.object_at(c.x,c.y)
		if o.get("id",-2)!=selected: selected=-1

func _pointer_move(pos: Vector2) -> void:
	if not moving: return
	if pointer_start.distance_to(pos)>10: dragged=true
	if screen=="restaurant" and modal=="" and editing and selected<0 and drag_kind=="" and pressed_action=="":
		# The exhibition floor fits one screen; small bounded panning keeps fixed scale.
		pan=(pan+pos-pointer_last).clamp(Vector2(-25,-36),Vector2(25,36))
	pointer_last=pos

func _pointer_up(pos: Vector2) -> void:
	if not moving: return
	moving=false
	if drag_kind!="" and dragged:
		var c:=_cell(pos)
		if model.place(drag_kind,c.x,c.y):
			audio.play("build")
			var o:Dictionary=model.object_at(c.x,c.y)
			selected=int(o.get("id",-1))
			if drag_kind=="belt":
				last_path=selected; path_start=selected
			if drag_kind=="chef":
				selected_recipe="cucumber"; modal="recipes"
			_save()
		else: _notify("Choose an empty, cleared floor cell.")
		drag_kind=""; pressed_action=""; return
	drag_kind=""
	if pressed_action!="":
		if not dragged: _action(pressed_action,pressed_data)
		pressed_action=""; return
	if modal!="": return
	if screen=="restaurant":
		var c:=_cell(pos)
		if c.x<0 or c.y<0 or c.x>=8 or c.y>=9: return
		if editing and selected>=0 and dragged:
			if model.move_object(selected,c.x,c.y):
				audio.play("build"); _save()
			else: _notify("That cell is occupied or uncleared.")
			return
		if dragged: return
		if not model.is_floor(c.x,c.y):
			modal="expand"; return
		var o:Dictionary=model.object_at(c.x,c.y)
		if editing:
			if layer==2:
				_notify("Choose Floor in the tray to change the room.")
				return
			if last_path>=0:
				var prev:Dictionary=model.get_object(last_path)
				if not prev.is_empty() and absi(c.x-int(prev.x))+absi(c.y-int(prev.y))==1:
					if o.is_empty() and model.place("belt",c.x,c.y): o=model.object_at(c.x,c.y)
					if o.get("kind")=="belt" and model.connect_belt(last_path,int(o.id)):
						last_path=int(o.id); selected=last_path; audio.play("build")
						if last_path==path_start: last_path=-1; selected=-1; path_start=-1
						_save(); return
				last_path=-1; path_start=-1
			selected=int(o.get("id",-1))
		else:
			if o.get("kind")=="chef":
				selected=int(o.id); modal="chef"
				meta.tutorial=maxi(2,int(meta.tutorial))

func _cell(pos: Vector2) -> Vector2i:
	var local:Vector2=(pos-_restaurant_origin()-ORIGIN-pan)/_grid_step()
	return Vector2i(floori(local.x),floori(local.y))

func _action(action: String, data: Variant=null) -> void:
	audio.play("click")
	match action:
		"play":
			if not restored_dive.is_empty(): _launch(restored_dive)
			elif not result.is_empty(): _change("results")
			elif meta.intro_seen: _change("restaurant")
			else: _change("intro")
		"finish_intro": _finish_intro()
		"close": modal=""
		"settings": modal="settings"
		"help": modal="help"
		"setting":
			meta[data]=not meta[data]
			audio.configure(meta.sound,meta.music)
			_save()
		"credits": modal="credits"
		"reset_confirm": modal="reset"
		"reset":
			model=Restaurant.new()
			meta={"charge":1.0,"salvage":0,"upgrades":{"hull":0,"harpoon":0,"collector":0},"intro_seen":false,"tutorial":0,"dives":0,"new_recipes":[],"completed":[],"sound":true,"music":true,"haptics":true,"reduced_motion":false,"pending_coins":0.0,"floor_style":0}
			restored_dive={}; result={}; editing=false; selected=-1; pan=Vector2.ZERO
			audio.configure(true,true); _change("intro"); _save()
		"shop": _change("shop")
		"workshop": _change("workshop")
		"restaurant": pan=Vector2.ZERO; _change("restaurant")
		"dock":
			if float(meta.charge)>=1:
				editing=false; _change("prep")
			else:
				var remaining:int=ceili((1-float(meta.charge))*float(balance.charge_seconds))
				_notify("Charging · %d:%02d until full" % [remaining/60,remaining%60])
		"route": selected_route=int(data)
		"launch": _launch()
		"edit": editing=true; selected=-1; inventory_kind=""
		"live": editing=false; selected=-1; last_path=-1; path_start=-1; _save()
		"layer": layer=int(data); selected=-1; last_path=-1
		"inventory": _notify("Drag this item from the tray onto the floor.")
		"deselect": selected=-1; last_path=-1; path_start=-1
		"rotate":
			model.rotate_object(selected); audio.play("build"); _save()
		"store":
			model.remove_object(selected); selected=-1; last_path=-1; audio.play("build"); _save()
		"crew":
			for o in model.data.objects:
				if o.kind=="chef": selected=int(o.id); modal="chef"; break
		"recipes":
			var chef:Dictionary=model.get_object(selected)
			selected_recipe=str(chef.get("recipe","cucumber"))
			if selected_recipe=="": selected_recipe="cucumber"
			modal="recipes"
		"inspect_recipe":
			selected_recipe=str(data)
			meta.new_recipes.erase(selected_recipe)
			_save()
		"prepare":
			if model.assign_recipe(selected,selected_recipe):
				modal=""; board_shake=0.7; audio.play("build"); _notify("Now preparing "+str(balance.recipes[selected_recipe].name)); _save()
		"chef_upgrade":
			if model.upgrade_chef(selected):
				audio.play("upgrade"); _haptic(); _save()
		"buy":
			if model.buy(str(data)):
				audio.play("build"); _notify("Added to your tray. Arrange to place it."); _save()
			else: _notify("Your crew is full. Clear more floor for room.")
		"floor":
			if meta.get("mint_floor_owned",false):
				meta.floor_style=1-int(meta.floor_style); audio.play("build"); _save()
			else: _notify("Find the sea-glass floor in the corner shop.")
		"buy_floor":
			if model.data.coins>=120 and not meta.get("mint_floor_owned",false):
				model.data.coins-=120; meta.mint_floor_owned=true
				audio.play("upgrade"); _notify("Sea-glass unlocked in the Floor palette"); _save()
		"expand":
			if model.expand():
				modal=""; audio.play("build"); _notify("More room for your little kitchen."); _save()
		"equipment":
			var cfg:Dictionary=balance.equipment[data]
			var lvl:int=int(meta.upgrades[data]); var cost:int=int(cfg.cost)*(lvl+1)
			if lvl<int(cfg.cap) and int(meta.salvage)>=cost:
				meta.salvage-=cost; meta.upgrades[data]=lvl+1
				audio.play("upgrade"); _haptic(); _save()
		"results": _change("results"); _save()
		"results_home":
			result={}; pan=Vector2.ZERO; _change("restaurant")
			if int(meta.get("return_notice",0))>0:
				_notify("+%d coins from service while you explored" % int(meta.return_notice))
				meta.return_notice=0
			_save()

func _launch(saved: Dictionary={}) -> void:
	if saved.is_empty() and float(meta.charge)<1: return
	var script=load("res://scripts/expedition.gd")
	dive=script.new()
	_change("dive")
	add_child(dive)
	dive.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dive.finished.connect(_dive_finished)
	dive.sound_requested.connect(func(id):
		audio.play(id)
		if id=="hit": _haptic())
	var gear:Dictionary=meta.upgrades.duplicate(true)
	gear["reduced_motion"]=bool(meta.reduced_motion)
	if saved.is_empty():
		meta.charge=0.0
		meta.pending_coins=0.0
		dive.setup(selected_route,gear,int(meta.dives)==0,saved)
	else:
		dive.setup(int(saved.get("route",selected_route)),gear,false,saved)
		dive.suspend()
	restored_dive={}
	editing=false
	_save()

func _dive_finished(receipt: Dictionary) -> void:
	if not is_instance_valid(dive): return
	result=receipt.duplicate(true)
	var species:String=result.get("species","salmon")
	var is_new:bool=bool(result.get("caught",false)) and species not in model.data.recipes
	result.repeat_bonus=12 if bool(result.get("caught",false)) and not is_new else 0
	result.total=int(result.get("pickups",0))+int(result.get("completion_bonus",0))+int(result.repeat_bonus)
	meta.salvage+=int(result.total)
	if is_new:
		model.data.recipes.append(species)
		meta.new_recipes.append(species)
	if result.get("outcome")=="complete" and int(result.get("route",selected_route)) not in meta.completed:
		meta.completed.append(int(result.get("route",selected_route)))
	meta.dives+=1
	meta.tutorial=3
	var earned:int=int(meta.pending_coins)
	model.data.coins+=float(meta.pending_coins)
	meta.pending_coins=0.0
	if is_instance_valid(dive):
		dive.queue_free()
		dive=null
	meta["return_notice"]=earned
	_change("cutscene" if is_new else "results")
	_save()
	audio.play("catch" if is_new else "win")

func _back() -> void:
	if screen=="dive":
		if is_instance_valid(dive): dive.suspend()
	elif modal!="": modal=""
	elif screen in ["shop","workshop","prep"]: pan=Vector2.ZERO; _change("restaurant")
	elif screen=="restaurant" and editing:
		editing=false; selected=-1; last_path=-1; _save()
	elif screen=="restaurant": modal="settings"
	elif screen=="intro": _finish_intro()
	elif screen=="reveal": _change("results")

func _notify(message: String) -> void:
	toast=message; toast_time=3.6

func _haptic() -> void:
	if meta.haptics and OS.has_feature("mobile"): Input.vibrate_handheld(22)

func _credits() -> void:
	_panel(Rect2(45,115,630,1090),PAPER,28,INK,true)
	_center("Made with care",333,178,38,INK,true)
	_button(Rect2(584,137,62,62),"×","settings",null,PAPER,true,35)
	_paragraph("Original illustrations and music created for this exhibition.
Type: Nunito by Vernon Adams and contributors; Delius by Natalia Raices. Licensed under the SIL Open Font License 1.1. Font licenses are included with the game.",Rect2(85,232,550,220),22)
	_paragraph(FileAccess.get_file_as_string("res://assets/GODOT-LICENSE.txt"),Rect2(85,460,550,704),16)
