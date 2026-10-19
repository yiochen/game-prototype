class_name SushiWorldEffect2D
extends Node2D
## Native 2D world cues. No Blender geometry, material or directional lighting.
## A Godot scene may drive phase/state/direction, or use the catalog's baked PNGs.
@export_enum("attack-swirl", "attack-lateral-current", "eel-warning-strip", "eel-lightning-symbol", "eel-discharge") var effect: String = "attack-swirl"
@export_enum("windup", "active", "recovery") var state: String = "active"
@export_enum("N", "E", "S", "W") var direction: String = "S"
@export_range(0.0, 1.0) var phase: float = 0.0
@export var autoplay := true

func _process(delta: float) -> void:
	if autoplay:
		phase = fposmod(phase + delta, 1.0)
	queue_redraw()

func _draw() -> void:
	var fade := 1.0
	if state == "windup": fade = 0.25 + 0.65 * phase
	if state == "recovery": fade = 1.0 - phase * 0.9
	var aqua := Color(0.60, 0.96, 1.0, fade)
	var amber := Color(1.0, 0.65, 0.12, fade)
	var rotation_angle: float = {"N": PI, "E": -PI / 2.0, "S": 0.0, "W": PI / 2.0}.get(direction, 0.0)
	draw_set_transform(Vector2.ZERO, rotation_angle)
	if effect == "eel-warning-strip":
		draw_rect(Rect2(-27, -155, 54, 310), Color(0.95, 0.48, 0.05, fade * 0.15))
		for i in range(12):
			var y := -151.0 + i * 25.0 + phase * 4.0
			draw_line(Vector2(-26, y), Vector2(26, y + 20), amber, 3.0, true)
		draw_line(Vector2(-28, -155), Vector2(-28, 155), amber, 2.0, true)
		draw_line(Vector2(28, -155), Vector2(28, 155), amber, 2.0, true)
	elif effect == "eel-lightning-symbol":
		var p := PackedVector2Array([Vector2(3,-48),Vector2(-27,5),Vector2(-3,2),Vector2(-12,48),Vector2(31,-13),Vector2(9,-9)])
		draw_colored_polygon(p, amber)
		var edge := PackedVector2Array(p)
		edge.append(p[0])
		draw_polyline(edge, Color(1.0, 226.0/255.0, 104.0/255.0, (150.0 + 80.0 * sin(phase * TAU)) / 255.0 * fade), 2.0, true)
	elif effect == "eel-discharge":
		for i in range(7):
			var angle := i * TAU / 7.0 + phase * 0.13
			var ray := Vector2.from_angle(angle)
			var side := ray.orthogonal()
			var p := PackedVector2Array([ray*12, ray*30 + side*9, ray*41-side*8, ray*(62+sin(phase*TAU+i)*8)])
			draw_polyline(p, aqua, 4.0, true)
	elif effect == "attack-lateral-current":
		for i in range(5):
			var y := -40.0 + i * 20.0
			var x := -90.0 + phase * 50.0
			var p := PackedVector2Array([Vector2(x,y+4),Vector2(x+40,y-3),Vector2(x+90,y),Vector2(x+140,y-4)])
			draw_polyline(p, aqua, 3.0 + i % 2, true)
			draw_polyline(PackedVector2Array([Vector2(x+122,y-17),Vector2(x+140,y-4),Vector2(x+120,y+8)]), aqua, 4.0, true)
	else:
		for strand in range(3):
			var p := PackedVector2Array()
			for step in range(60):
				var t := step / 59.0
				var angle := t * TAU * 1.4 + phase * TAU + strand * TAU / 3.0
				p.append(Vector2(cos(angle), sin(angle)*0.55) * (12.0 + t*(49.0 + strand*4.0)))
			draw_polyline(p, aqua, 3.0, true)
