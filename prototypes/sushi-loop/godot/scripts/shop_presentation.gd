extends Control
## Approved issue 18 composition, shared by gameplay and --shop-gallery.
const FloorPattern = preload("res://scripts/floor_pattern.gd")
const Book = preload("res://scripts/shop_book.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const PopupSkin = preload("res://scripts/maple_popup_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const EditorUI = preload("res://scripts/editor_presentation.gd")
const ArtBook = preload("res://scripts/art_book.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const GameButton = preload("res://scripts/game_button.gd")
const INK := Color("592c10")
signal purchase_requested(request: Dictionary, source: Rect2)
signal closed
var wood = Wood.new()
var art = ArtBook.new()
var font: Font
var state: Dictionary = {}
var unit := 1.0
var area := Rect2()
var safe_top := 0.0
var reduced_motion := false
var interaction_blocked := false
var panel: Panel
var face: TextureRect
var catalog_backing: Panel
var catalog_shade: ColorRect
var catalog: ScrollContainer
var content: VBoxContainer
var heading: Label
var balance: Label
var coin: TextureRect
var close_button: Button
var bag_button: Button
var bag_icon: TextureRect
var waves: Control
var rows: Dictionary = {}
var flights: Array[Control] = []
var flight_tweens: Array[Tween] = []
var bag_tween: Tween
var touch_index := -1
var touch_origin := Vector2.ZERO
var touch_scroll := 0
var touch_offer := ""
var touch_dragged := false
var focused_before: Control
var signature := ""

class Waves extends Control:
	var wood_skin
	func _draw() -> void:
		wood_skin.draw_asset(self,"footer-waves",Vector2.ZERO,size.x/664.0)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	font = Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	art.reload()
	var scrim := ColorRect.new()
	scrim.color = Color(.25,.16,.07,.20)
	scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(scrim)
	panel = Panel.new()
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.accessibility_name = "Shop"
	add_child(panel)
	face = PopupSkin.make_face(panel,wood.texture("wood-grain"))
	heading = _label(panel);heading.text = "Shop"
	balance = _label(panel);balance.accessibility_name = "Shop coin balance"
	coin = _image(panel,UISkin.cash_icon())
	catalog_backing = Panel.new()
	catalog_backing.mouse_filter = Control.MOUSE_FILTER_STOP
	catalog_backing.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	panel.add_child(catalog_backing)
	catalog_shade = PopupSkin.inner_shadow(catalog_backing)
	catalog = ScrollContainer.new()
	catalog.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	catalog.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	catalog.follow_focus = true
	catalog.focus_mode = Control.FOCUS_ALL
	catalog.accessibility_name = "Shop catalog"
	catalog_backing.add_child(catalog)
	content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation",0)
	catalog.add_child(content)
	close_button = _button("×","Close Shop",panel)
	close_button.pressed.connect(dismiss)
	bag_button = _button("","Back to inventory",panel)
	bag_button.tooltip_text = "Back to inventory"
	bag_button.pressed.connect(dismiss)
	bag_icon = _image(bag_button,load("res://assets/ui/shop-bag.svg"))
	waves = Waves.new();waves.wood_skin = wood;waves.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(waves)
	panel.move_child(waves,panel.get_child_count()-3)
	hide()

func _label(parent: Node) -> Label:
	var value := Label.new()
	value.add_theme_font_override("font",font)
	value.add_theme_color_override("font_color",INK)
	value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	value.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	parent.add_child(value)
	return value

func _button(text: String, accessible: String, parent: Node) -> Button:
	var value := Button.new()
	value.text = text;value.accessibility_name = accessible
	value.add_theme_font_override("font",font)
	for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]: value.add_theme_color_override(key,INK)
	value.add_theme_color_override("font_disabled_color",Color("806b52"))
	parent.add_child(value)
	return value

func _image(parent: Node, texture: Texture2D) -> TextureRect:
	var value := TextureRect.new()
	value.texture = texture
	value.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	value.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(value)
	return value

func open(value: Dictionary) -> bool:
	if value.get("mode") != "edit" or interaction_blocked: return false
	focused_before = get_viewport().gui_get_focus_owner()
	state = value
	signature = ""
	show()
	if rows.is_empty(): _build_rows()
	catalog.scroll_vertical = 0
	refresh(value)
	layout(area,safe_top)
	close_button.grab_focus(true)
	return true

func _build_rows() -> void:
	for row in rows.values():
		content.remove_child(row.row);row.row.queue_free()
	rows.clear()
	for offer in state.shop.offers:
		var row := Control.new()
		row.mouse_filter = Control.MOUSE_FILTER_PASS
		row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		content.add_child(row)
		var preview: Control = FloorPattern.new() if offer.kind=="floor" else EditorUI.ItemPreview.new()
		if offer.kind!="floor":preview.art = art;preview.trim_goods = true
		preview.entry = offer;preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(preview)
		var name_label := _label(row);name_label.text = offer.name
		var description := _label(row)
		description.size.x = 296*unit
		description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		description.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
		description.text = offer.description
		description.add_theme_color_override("font_color",Color("866347"))
		var stock := _label(row);stock.add_theme_color_override("font_color",Color("80613c"))
		var buy := GameButton.new();buy.tone = GameButton.Tone.MAPLE;buy.radius = 40.0;buy.caption_px = 30.0
		buy.text = str(int(offer.cost));buy.cost = buy.text;buy.captioned = false;buy.cost_icon = coin.texture
		buy.accessibility_name = "Buy %s for %s coins" % [offer.name,int(offer.cost)];row.add_child(buy)
		buy.pressed.connect(func(): _request(str(offer.id)))
		var owned := _label(row);owned.text="Owned";owned.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		var line := ColorRect.new();line.color = Color(.65,.47,.28,.20);line.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(line)
		rows[offer.id] = {"row":row,"preview":preview,"name":name_label,"description":description,"stock":stock,"buy":buy,"line":line,"offer":offer,"owned":owned}

func refresh(value: Dictionary) -> void:
	if not visible: return
	state = value
	if rows.keys() != value.shop.offers.map(func(o):return o.id):
		_build_rows();layout(area,safe_top)
	var next_signature := JSON.stringify([value.coins,value.shop,interaction_blocked])
	if signature == next_signature: return
	signature = next_signature
	balance.text = str(int(value.coins))
	balance.accessibility_description = "%s coins" % int(value.coins)
	for offer in value.shop.offers:
		var row: Dictionary = rows[offer.id]
		row.offer = offer
		var sold: bool = offer.remaining != null and int(offer.remaining) == 0
		row.stock.text = "" if offer.kind=="floor" else "Level %d → %d" % [int(offer.level) + 1, int(offer.level) + 2] if offer.kind=="tip_upgrade" else "Always available" if offer.remaining == null else "Sold out" if sold else "%s remaining" % int(offer.remaining)
		row.owned.visible = offer.get("owned",false)
		row.buy.visible = not offer.get("owned",false)
		row.buy.disabled = interaction_blocked or offer.get("owned",false) or sold or int(value.coins) < int(offer.cost)
		row.buy.accessibility_description = "Sold out" if sold else "Not enough coins" if int(value.coins) < int(offer.cost) else "Upgrades the tip jar" if offer.kind=="tip_upgrade" else "Adds one to inventory"
		row.preview.modulate.a = .45 if sold else 1.0
	close_button.disabled = interaction_blocked
	bag_button.disabled = interaction_blocked

func _request(id: String) -> void:
	if interaction_blocked or not visible or not rows.has(id) or rows[id].buy.disabled: return
	var request := {"type":"shop_purchase","offer_id":id,"expected_sequence":state.shop.purchase_sequence}
	if rows[id].offer.kind=="floor":request={"type":"floor_purchase","offer_id":id,"expected_sequence":state.floor_styles.purchase_sequence,"rotation":state.floor_styles.rotation}
	if rows[id].offer.kind=="tip_upgrade":request={"type":"tip_jar_upgrade","offer_id":id,"expected_level":int(rows[id].offer.level)}
	purchase_requested.emit(request,rows[id].preview.get_global_rect())

func _text(label: Label, bounds: Rect2, pixels: float) -> void:
	label.add_theme_font_size_override("font_size",maxi(1,int(pixels*unit)))
	label.position = bounds.position*unit
	label.size = bounds.size*unit

func layout(value: Rect2, inset := 0.0) -> void:
	area = value;safe_top = inset
	if panel == null or value.size.x <= 0: return
	var physical := maxf(.001,get_viewport_transform().get_scale().x)
	var compact := size.x > size.y and size.y*physical < 600
	var width := value.size.x
	if compact: width = minf(size.x,320.0/physical)
	var frame := Rect2((size.x-width)*.5,value.position.y,width,value.size.y)
	unit = width/720.0
	var top := maxf(frame.position.y,inset)+(24 if compact else 52)*unit
	panel.position = Vector2(frame.position.x+24*unit,top)
	panel.size = Vector2(frame.size.x-48*unit,maxf(180*unit,frame.end.y-top-(26 if compact else 40)*unit))
	var shadow := PopupSkin.flat(Color.TRANSPARENT,32*unit)
	shadow.shadow_color = Color(.35,.18,.05,.20);shadow.shadow_size = int(8*unit);shadow.shadow_offset = Vector2(0,6)*unit
	panel.add_theme_stylebox_override("panel",shadow)
	PopupSkin.layout_face(face,panel.size,unit)
	var reference_width := panel.size.x/unit
	var header := 156.0 if compact else 200.0
	var footer := 150.0
	_text(balance,Rect2(82,24,reference_width-240,48),38)
	coin.position = Vector2(36,26)*unit;coin.size = Vector2(40,40)*unit
	_text(heading,Rect2(36,86,reference_width-160,64),52)
	if compact:
		_text(balance,Rect2(76,16,reference_width-230,42),34)
		coin.position = Vector2(32,18)*unit;coin.size = Vector2(36,36)*unit
		_text(heading,Rect2(32,70,reference_width-150,52),46)
	close_button.position = Vector2(reference_width-120,24 if not compact else 16)*unit
	PopupSkin.close_button(close_button,unit,physical)
	catalog_backing.position = Vector2(16,header)*unit
	catalog_backing.size = Vector2(reference_width-32,maxf(60,panel.size.y/unit-header-footer))*unit
	catalog_backing.add_theme_stylebox_override("panel",PopupSkin.flat(Color("fff3db"),32*unit))
	PopupSkin.layout_inner_shadow(catalog_shade,Rect2(Vector2.ZERO,catalog_backing.size),32*unit,unit)
	catalog.position = Vector2(20,0)*unit
	catalog.size = Vector2(catalog_backing.size.x-40*unit,catalog_backing.size.y)
	var row_width := catalog.size.x/unit
	for id in rows:
		var row: Dictionary = rows[id]
		# A description that wraps past two lines pushes the stock line down and
		# grows its row, so the two never overlap (the tip jar's copy wraps to 3+).
		var text_w := row_width-304
		var description_h := font.get_multiline_string_size(row.description.text,HORIZONTAL_ALIGNMENT_LEFT,text_w*unit,maxi(1,int(21*unit))).y/unit
		var stock_y := maxf(153.0,86.0+description_h+6.0)
		var row_h := maxf(230.0,stock_y+77.0)
		var drop := (row_h-230.0)*.5
		row.row.custom_minimum_size = Vector2(0,row_h)*unit
		row.row.size = Vector2(catalog.size.x,row_h*unit)
		row.preview.position = Vector2(0,38+drop)*unit;row.preview.size = Vector2(132,148)*unit;row.preview.queue_redraw()
		_text(row.name,Rect2(146,35,text_w,48),32)
		_text(row.description,Rect2(146,86,text_w,maxf(62.0,description_h)),21)
		_text(row.stock,Rect2(146,stock_y,text_w,36),21)
		row.buy.position = Vector2(row_width-136,78+drop)*unit;row.buy.size = Vector2(136,90)*unit;row.buy.fit(unit,physical)
		_text(row.owned,Rect2(row_width-136,78+drop,136,90),27)
		row.line.position = Vector2(0,row_h-1)*unit;row.line.size = Vector2(row_width,maxf(1,unit))
	PopupSkin.round_button(bag_button,unit,physical,114)
	bag_button.position = Vector2(panel.size.x-144*unit,panel.size.y-138*unit)
	bag_icon.position = bag_button.size*.25;bag_icon.size = bag_button.size*.5
	waves.position = Vector2(32*unit,panel.size.y-64*unit);waves.size = Vector2(panel.size.x-212*unit,36*unit);waves.queue_redraw()

func purchased(id: String, source: Rect2) -> void:
	if not visible or not rows.has(id): return
	if reduced_motion: _pulse_bag();return
	var image = EditorUI.ItemPreview.new()
	image.entry = rows[id].offer;image.art = art;image.trim_goods = true;image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	image.size = Vector2(132,148)*unit
	image.pivot_offset = image.size*.5
	image.position = source.get_center()-global_position-image.size*.5
	add_child(image);image.queue_redraw();flights.append(image)
	var start: Vector2 = image.position
	var finish: Vector2 = bag_button.get_global_rect().get_center()-global_position-image.size*.5
	var lift := Vector2(lerpf(start.x,finish.x,.36),minf(start.y-120*unit,lerpf(start.y,finish.y,.2)))
	var tween := create_tween();flight_tweens.append(tween)
	tween.tween_method(func(t: float):
		if not is_instance_valid(image): return
		if t < .4:
			var f := ease(t/.4,1.6);image.position = start.lerp(lift,f);image.scale = Vector2.ONE*lerpf(1,.9,f);image.rotation = lerpf(0,deg_to_rad(-9),f)
		else:
			var f := ease((t-.4)/.6,.7);image.position = lift.lerp(finish,f);image.scale = Vector2.ONE*lerpf(.9,.12,f);image.rotation = lerpf(deg_to_rad(-9),deg_to_rad(8),f)
			image.modulate.a = 1-f*f
	,0.0,1.0,float(Book.definition().purchase_flight_seconds))
	tween.tween_callback(func():
		flights.erase(image);image.queue_free();_pulse_bag())
	tween.finished.connect(_prune_tweens)

func _pulse_bag() -> void:
	if is_instance_valid(bag_tween): bag_tween.kill()
	bag_icon.scale = Vector2.ONE;bag_icon.modulate.a = 1
	bag_icon.pivot_offset = bag_icon.size*.5
	bag_tween = create_tween()
	if reduced_motion:
		bag_icon.modulate.a = .65
		bag_tween.tween_property(bag_icon,"modulate:a",1.0,float(Book.definition().bag_pulse_seconds))
	else:
		bag_tween.tween_property(bag_icon,"scale",Vector2.ONE*1.13,.096)
		bag_tween.tween_property(bag_icon,"scale",Vector2.ONE,.144)

func cancel_interactions() -> void:
	touch_index = -1;touch_offer = "";touch_dragged = false
	for tween in flight_tweens:
		if is_instance_valid(tween): tween.kill()
	flight_tweens.clear()
	for image in flights:
		if is_instance_valid(image): image.queue_free()
	flights.clear()
	if is_instance_valid(bag_tween): bag_tween.kill()
	if bag_icon != null: bag_icon.scale = Vector2.ONE;bag_icon.modulate.a = 1
	var buttons: Array = [close_button,bag_button]
	for row in rows.values():
		row.buy.release()
		buttons.append(row.buy)
	for button in buttons:
		if not is_instance_valid(button): continue
		var disabled: bool = button.disabled
		button.disabled = true;button.disabled = disabled

func dismiss() -> void:
	if not visible or interaction_blocked: return
	cancel_interactions();hide();closed.emit()

func _input(event: InputEvent) -> void:
	if not visible or interaction_blocked: return
	if event is InputEventScreenTouch and event.pressed and catalog.get_global_rect().has_point(event.position):
		if touch_index != -1: get_viewport().set_input_as_handled();return
		touch_index = event.index;touch_origin = event.position;touch_scroll = catalog.scroll_vertical;touch_dragged = false;touch_offer = ""
		for id in rows:
			if rows[id].buy.get_global_rect().has_point(event.position) and not rows[id].buy.disabled:
				touch_offer = id;rows[id].buy.hold(true);break
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag and event.index == touch_index:
		var delta: Vector2 = event.position-touch_origin
		if delta.length()>10/maxf(.001,get_viewport_transform().get_scale().x): touch_dragged = true
		if touch_dragged:
			catalog.scroll_vertical = touch_scroll-int(delta.y)
			if rows.has(touch_offer): rows[touch_offer].buy.release()
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch and not event.pressed and event.index == touch_index:
		var id := touch_offer;var dragged := touch_dragged;touch_index = -1;touch_offer = ""
		if rows.has(id): rows[id].buy.release()
		if not event.canceled and not dragged and rows.has(id) and rows[id].buy.get_global_rect().has_point(event.position) and catalog.get_global_rect().has_point(event.position): _request(id)
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE: dismiss();get_viewport().set_input_as_handled()
		elif event.keycode == KEY_TAB:
			var targets: Array[Control] = [close_button,catalog]
			for row in rows.values():
				if not row.buy.disabled: targets.append(row.buy)
			targets.append(bag_button)
			var current := targets.find(get_viewport().gui_get_focus_owner())
			targets[posmod(current+(-1 if event.shift_pressed else 1),targets.size())].grab_focus()
			get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED,NOTIFICATION_WM_WINDOW_FOCUS_OUT] and is_node_ready(): cancel_interactions()

func _prune_tweens() -> void:
	flight_tweens = flight_tweens.filter(func(tween): return is_instance_valid(tween) and tween.is_running())

func _exit_tree() -> void:
	cancel_interactions()

