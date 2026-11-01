extends Control
## Exact deterministic 256px exports of the approved HTML/CSS pattern family.
static var textures: Dictionary = {}
var entry: Dictionary = {}
var selected := false
static func texture(id: String) -> Texture2D:
	if not textures.has(id): textures[id] = load("res://assets/ui/floor-patterns/%s.png"%id)
	return textures[id]
func _draw() -> void:
	var edge := minf(size.x,size.y)
	var bounds := Rect2((size-Vector2.ONE*edge)*.5,Vector2.ONE*edge)
	var frame := StyleBoxFlat.new();frame.bg_color=Color("fff0c8");frame.set_corner_radius_all(int(edge*.06));frame.shadow_color=Color("a67c4a");frame.shadow_size=1;frame.shadow_offset=Vector2(0,3*edge/66)
	draw_style_box(frame,bounds)
	bounds = bounds.grow(-maxf(1,edge/40))
	var tile := bounds.size*.5
	for y in range(2):
		for x in range(2): draw_texture_rect(texture(str(entry.get("style_id",entry.get("id","cream")))),Rect2(bounds.position+Vector2(x,y)*tile,tile),false)

	if selected: draw_circle(Vector2(size.x*.5,size.y+20*size.x/126.0),3*size.x/126.0,Color("7c4d2c"))
