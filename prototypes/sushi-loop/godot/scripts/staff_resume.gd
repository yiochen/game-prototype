extends Control
## Approved paper resume: native live text, source-calibrated paper, separate ink/prop.
const Art = preload("res://scripts/recipe_art.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const Wood = preload("res://scripts/wood_skin.gd")
signal hire_requested(id: String)
var offer: Dictionary = {}
var coins := 0
var full := false
var unit := 1.0
var narrow := false
var motion_offset := Vector2.ZERO
var font: Font
var wood = Wood.new()
var heading: Label
var occupation: Label
var background_text: Label
var eyebrow: Label
var portrait: Control
var names: Array[Label] = []
var values: Array[Label] = []
var hire_button: Button
var hire_word: Label
var budget: RichTextLabel
var coin: TextureRect
var imprint: Control
var stamp_text: Label
var stamp_prop: TextureRect
var paper: Texture2D = preload("res://assets/ui/staff/resume-paper.png")

class Head extends Control:
	var identity := "chef-lena"
	func _draw() -> void:
		var image = preload("res://scripts/recipe_art.gd").head(identity)
		draw_texture_rect_region(image,Rect2(Vector2.ZERO,size),Rect2(0,0,image.get_width(),image.get_width()*1.28))
class Ink extends Control:
	var texture: Texture2D = preload("res://assets/ui/staff/assigned-stamp.png")
	func _draw() -> void: draw_texture_rect(texture,Rect2(Vector2.ZERO,size),false)

func _ready() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	font = Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	eyebrow = label("APPLICATION")
	heading = label("")
	occupation = label(""); occupation.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	background_text = label(""); background_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	portrait = Head.new();portrait.mouse_filter = MOUSE_FILTER_IGNORE;add_child(portrait)
	for text in ["Cooking speed","Growth / level","Max level"]: names.append(label(text));values.append(label(""))
	hire_button = Button.new();hire_button.mouse_filter = MOUSE_FILTER_STOP;hire_button.accessibility_name = "Hire applicant";add_child(hire_button)
	hire_button.pressed.connect(func(): hire_requested.emit(str(offer.id)))
	hire_word = label("Hire",hire_button)
	budget = RichTextLabel.new();budget.bbcode_enabled = true;budget.scroll_active = false;budget.mouse_filter = MOUSE_FILTER_IGNORE;budget.add_theme_font_override("normal_font",font);hire_button.add_child(budget)
	coin = TextureRect.new();var coin_image:=AtlasTexture.new();coin_image.atlas=wood.texture("coin-emblem");coin_image.region=Rect2(32,32,108,108);coin.texture=coin_image;coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE;coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED;coin.mouse_filter = MOUSE_FILTER_IGNORE;hire_button.add_child(coin)
	imprint = Ink.new();imprint.mouse_filter = MOUSE_FILTER_IGNORE;add_child(imprint);stamp_text = label("Hired",imprint);stamp_text.add_theme_color_override("font_color",Color("c54632"));imprint.modulate.a = 0
	stamp_prop = TextureRect.new();stamp_prop.texture = preload("res://assets/ui/staff/hiring-stamp.png");stamp_prop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE;stamp_prop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED;stamp_prop.mouse_filter = MOUSE_FILTER_IGNORE;add_child(stamp_prop);stamp_prop.modulate.a = 0
	layout()

func label(text: String, parent: Node = self) -> Label:
	var result := Label.new();result.text = text;result.add_theme_font_override("font",font);result.add_theme_color_override("font_color",Color("592c10"));result.mouse_filter = MOUSE_FILTER_IGNORE;parent.add_child(result);return result
func text_at(node: Label, box: Rect2, pixels: float, color := Color("592c10")) -> void:
	node.add_theme_color_override("font_color",color)
	if node.autowrap_mode != TextServer.AUTOWRAP_OFF:
		node.add_theme_font_size_override("font_size",maxi(1,int(pixels*unit)));node.position=box.position*unit;node.size=box.size*unit
	else: UISkin.layout_caption(node,Rect2(box.position*unit,box.size*unit),maxi(1,int(pixels*unit)))
func layout() -> void:
	if not is_node_ready(): return
	var width := size.x/unit
	var pad := 14.0 if narrow else 18.0
	var head_width := 62.0 if narrow else 73.0
	var head_height := 80.0 if narrow else 94.0
	var top := 16.0 if narrow else 18.0
	portrait.position = Vector2(pad,top)*unit;portrait.size=Vector2(head_width,head_height)*unit;portrait.identity=str(offer.get("art_id","chef-lena"));portrait.queue_redraw()
	var left := pad+head_width+8
	text_at(eyebrow,Rect2(left,top+10,width-left-pad,15),8,Color("9c794f"))
	heading.text = str(offer.get("name",""));text_at(heading,Rect2(left,top+28,width-left-pad,29),20 if narrow else 22)
	occupation.text = str(offer.get("role",""));text_at(occupation,Rect2(left,top+60,width-left-pad,39),10 if narrow else 11,Color("916b46"))
	background_text.text = str(offer.get("background",""));text_at(background_text,Rect2(pad,top+head_height+12,width-pad*2,53),11 if narrow else 12,Color("805e3f"))
	var target_height:=maxf(48*unit,44.01/maxf(.001,get_viewport_transform().get_scale().x))
	var hire_top:=(size.y-18*unit-target_height)/unit
	var stats_y := minf(173.0 if narrow else 204.0,hire_top-67)
	background_text.size.y=minf(53,stats_y-(top+head_height+12)-6)*unit
	var step := (width-pad*2)/3.0
	values[0].text = "%.1f×" % float(offer.get("cooking_speed",1.0))
	values[1].text = "+%s%%" % int(round(float(offer.get("growth_rate",.1))*100))
	values[2].text = str(int(offer.get("level_cap",12)))
	for i in range(3):
		text_at(names[i],Rect2(pad+i*step,stats_y+5,step,18),8 if narrow else 10,Color("98754f"))
		text_at(values[i],Rect2(pad+i*step,stats_y+27,step,28),18 if narrow else 19)
	hire_button.custom_minimum_size = Vector2.ZERO
	hire_button.position = Vector2(pad*unit,hire_top*unit);hire_button.size = Vector2((width-pad*2)*unit,target_height)
	var style_scale := unit*390.0/720.0
	for treatment in ["normal","hover","pressed","disabled"]: hire_button.add_theme_stylebox_override(treatment,wood.style("hud-cream-normal" if treatment=="disabled" else "hud-live-pressed" if treatment=="pressed" else "hud-live-normal",style_scale))
	hire_button.add_theme_stylebox_override("focus",StyleBoxEmpty.new())
	hire_button.disabled = full or coins<int(offer.get("cost",0))
	hire_button.accessibility_name = "Hire %s for %s coins%s" % [offer.get("name",""),offer.get("cost",0),", %s coins available" % coins if coins<int(offer.get("cost",0)) else ", roster full" if full else ""]
	var poor := coins<int(offer.get("cost",0));var ink := Color("927553") if hire_button.disabled else Color("fff9ed")
	text_at(hire_word,Rect2(16,0,(width-pad*2)*.43,target_height/unit),18,ink)
	coin.position=Vector2((width-pad*2)*.48,(target_height/unit-22)*.5)*unit;coin.size=Vector2(22,22)*unit
	budget.position=Vector2((width-pad*2)*.48+28,(target_height/unit-28)*.5)*unit;budget.size=Vector2((width-pad*2)*.52-32,32)*unit;budget.add_theme_font_size_override("normal_font_size",int(17*unit));budget.add_theme_color_override("default_color",ink)
	budget.text = "%s / [color=#b84432]%s[/color]" % [coins,int(offer.get("cost",0))] if poor else str(int(offer.get("cost",0)))
	imprint.size=Vector2(minf(176,width*.66),minf(176,width*.66)*488.0/2048)*unit;imprint.pivot_offset=imprint.size*.5;imprint.position=size*.52-imprint.size*.5;imprint.position.x=size.x*.5-imprint.size.x*.5;imprint.rotation=deg_to_rad(-12);imprint.queue_redraw()
	UISkin.layout_caption(stamp_text,Rect2(Vector2.ZERO,imprint.size),int(28*unit))
	stamp_prop.size=Vector2(minf(172,width*.56),minf(172,width*.56)*876.0/964)*unit;stamp_prop.position=Vector2((size.x-stamp_prop.size.x)*.5,size.y*.52-stamp_prop.size.y)
	queue_redraw()
func _draw() -> void:
	var source := paper.get_size();var edge := 36*unit
	var sx := [0.0,170.0,source.x-170,source.x];var sy := [0.0,170.0,source.y-170,source.y]
	var dx := [0.0,edge,size.x-edge,size.x];var dy := [0.0,edge,size.y-edge,size.y]
	for y in range(3):
		for x in range(3): draw_texture_rect_region(paper,Rect2(dx[x],dy[y],dx[x+1]-dx[x],dy[y+1]-dy[y]),Rect2(sx[x],sy[y],sx[x+1]-sx[x],sy[y+1]-sy[y]))
	if is_node_ready():
		var pad := (14.0 if narrow else 18.0)*unit
		var y := minf(173.0 if narrow else 204.0,hire_button.position.y/unit-67)*unit
		draw_line(Vector2(pad,y),Vector2(size.x-pad,y),Color("dac69e"),unit)
		draw_line(Vector2(pad,hire_button.position.y-12*unit),Vector2(size.x-pad,hire_button.position.y-12*unit),Color("dac69e"),unit)
