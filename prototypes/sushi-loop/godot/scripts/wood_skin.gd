extends RefCounted
## Transparent HTML exports. Fixed corner pixels scale uniformly; plain spans tile.
const DIRECTORY := "res://assets/ui/wood-editor/"
var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "manifest.json"))
var textures: Dictionary = {}
var styles: Dictionary = {}
var icons: Dictionary = {}

class Surface extends StyleBox:
	var texture: Texture2D
	var entry: Dictionary
	var unit: float
	func _init(image: Texture2D, data: Dictionary, scale_value: float) -> void:
		texture = image
		entry = data
		unit = scale_value
	func _draw(canvas: RID, rect: Rect2) -> void:
		var expansion: Array = entry.stylebox_expand_margins_ltrb
		var target := rect.grow_individual(float(expansion[0])*unit, float(expansion[1])*unit, float(expansion[2])*unit, float(expansion[3])*unit)
		var cuts: Array = entry.variants["2x"].get("nine_patch_margins_ltrb", [0,0,0,0])
		var dimensions := texture.get_size()
		var sx := [0.0, float(cuts[0]), dimensions.x-float(cuts[2]), dimensions.x]
		var sy := [0.0, float(cuts[1]), dimensions.y-float(cuts[3]), dimensions.y]
		var dx := [target.position.x, target.position.x+float(cuts[0])*unit/2, target.end.x-float(cuts[2])*unit/2, target.end.x]
		var dy := [target.position.y, target.position.y+float(cuts[1])*unit/2, target.end.y-float(cuts[3])*unit/2, target.end.y]
		for row in range(3):
			for col in range(3):
				var src := Rect2(sx[col],sy[row],sx[col+1]-sx[col],sy[row+1]-sy[row])
				var dst := Rect2(dx[col],dy[row],dx[col+1]-dx[col],dy[row+1]-dy[row])
				if not src.has_area() or not dst.has_area(): continue
				var tile_x: bool = col == 1 and entry.resize != "uniform_only"
				var tile_y: bool = row == 1 and entry.resize == "nine_patch_tile_center"
				var pitch := Vector2(src.size.x*unit/2 if tile_x else dst.size.x, src.size.y*unit/2 if tile_y else dst.size.y)
				var y := dst.position.y
				while y < dst.end.y - 0.001:
					var x := dst.position.x
					var h := minf(pitch.y,dst.end.y-y)
					while x < dst.end.x - 0.001:
						var w := minf(pitch.x,dst.end.x-x)
						texture.draw_rect_region(canvas,Rect2(x,y,w,h),Rect2(src.position,Vector2(src.size.x*w/pitch.x,src.size.y*h/pitch.y)))
						x += pitch.x
					y += pitch.y

func texture(identity: String) -> Texture2D:
	if not textures.has(identity): textures[identity] = load(DIRECTORY + identity + ".png")
	return textures[identity]

func style(identity: String, unit: float) -> StyleBox:
	var key := "%s:%0.6f" % [identity,unit]
	if not styles.has(key): styles[key] = Surface.new(texture(identity),manifest.assets[identity],unit)
	return styles[key]

func icon(identity: String) -> Texture2D:
	if icons.has(identity): return icons[identity]
	var result := AtlasTexture.new()
	result.atlas = texture("icon-" + identity)
	result.region = Rect2(32,32,64,64)
	result.filter_clip = true
	icons[identity] = result
	return result

func draw_asset(canvas: CanvasItem, identity: String, origin: Vector2, unit: float) -> void:
	var asset: Dictionary = manifest.assets[identity]
	var offset: Array = asset.draw_offset
	var dimensions: Array = asset.logical_size
	canvas.draw_texture_rect(texture(identity),Rect2(origin+Vector2(float(offset[0]),float(offset[1]))*unit,Vector2(float(dimensions[0]),float(dimensions[1]))*unit),false)
