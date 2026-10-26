extends RefCounted
## Foreground clipping contours of the unchanged approved 1728 x 1344 gate.
## Source pixels/registration are reused directly; no replacement artwork or
## runtime image readback. Contours retain cloth waves, straps and open seams.
const ROOF_BOTTOM := 497.0
const PANELS := [
	[
		Vector2(491, 513), Vector2(492, 512), Vector2(498, 512), Vector2(513, 515), Vector2(514, 499),
		Vector2(516, 497), Vector2(535, 497), Vector2(537, 498), Vector2(538, 520), Vector2(543, 520),
		Vector2(544, 521), Vector2(565, 520), Vector2(602, 512), Vector2(625, 513), Vector2(640, 517),
		Vector2(655, 520), Vector2(662, 520), Vector2(663, 521), Vector2(682, 520), Vector2(683, 499),
		Vector2(685, 497), Vector2(705, 497), Vector2(706, 498), Vector2(707, 515), Vector2(722, 512),
		Vector2(728, 512), Vector2(729, 513), Vector2(729, 812), Vector2(698, 826), Vector2(685, 830),
		Vector2(673, 831), Vector2(672, 832), Vector2(652, 831), Vector2(622, 824), Vector2(599, 824),
		Vector2(568, 831), Vector2(547, 832), Vector2(525, 827), Vector2(491, 812),
	],
	[
		Vector2(744, 515), Vector2(746, 512), Vector2(752, 512), Vector2(767, 515), Vector2(768, 498),
		Vector2(769, 497), Vector2(788, 497), Vector2(790, 498), Vector2(791, 520), Vector2(796, 520),
		Vector2(797, 521), Vector2(819, 520), Vector2(856, 512), Vector2(879, 513), Vector2(898, 518),
		Vector2(908, 520), Vector2(915, 520), Vector2(916, 521), Vector2(936, 520), Vector2(937, 497),
		Vector2(957, 497), Vector2(959, 498), Vector2(960, 515), Vector2(975, 512), Vector2(982, 512),
		Vector2(983, 515), Vector2(983, 810), Vector2(982, 813), Vector2(954, 825), Vector2(938, 830),
		Vector2(927, 831), Vector2(926, 832), Vector2(905, 831), Vector2(875, 824), Vector2(852, 824),
		Vector2(822, 831), Vector2(801, 832), Vector2(785, 829), Vector2(773, 825), Vector2(747, 814),
		Vector2(745, 813), Vector2(744, 806),
	],
	[
		Vector2(998, 513), Vector2(999, 512), Vector2(1005, 512), Vector2(1020, 515), Vector2(1021, 498),
		Vector2(1022, 497), Vector2(1043, 497), Vector2(1044, 499), Vector2(1045, 520), Vector2(1064, 521),
		Vector2(1065, 520), Vector2(1072, 520), Vector2(1087, 517), Vector2(1102, 513), Vector2(1124, 512),
		Vector2(1162, 520), Vector2(1183, 521), Vector2(1184, 520), Vector2(1189, 520), Vector2(1190, 498),
		Vector2(1192, 497), Vector2(1212, 497), Vector2(1213, 498), Vector2(1214, 515), Vector2(1228, 512),
		Vector2(1235, 512), Vector2(1236, 513), Vector2(1236, 812), Vector2(1202, 827), Vector2(1180, 832),
		Vector2(1159, 831), Vector2(1128, 824), Vector2(1106, 824), Vector2(1075, 831), Vector2(1054, 832),
		Vector2(1053, 831), Vector2(1042, 830), Vector2(1029, 826), Vector2(998, 812),
	],
]

static func draw_front(view: Control, base: Vector2) -> void:
	if view._record_only or view._collect_ground_shadows: return
	var frame: Dictionary = view.art.frame_data("backdrop-entrance")
	if frame.is_empty(): return
	var texture: Texture2D = frame.texture
	var rect: Rect2 = view.art.registered_rect("backdrop-entrance", base, view.cell)
	var scale_value := rect.size / texture.get_size()
	view.draw_texture_rect_region(texture, Rect2(rect.position, Vector2(rect.size.x, ROOF_BOTTOM * scale_value.y)), Rect2(0, 0, texture.get_width(), ROOF_BOTTOM))
	for panel in PANELS:
		var points := PackedVector2Array()
		var uvs := PackedVector2Array()
		for point in panel:
			points.append(rect.position + point * scale_value)
			uvs.append(point / texture.get_size())
		view.draw_polygon(points, PackedColorArray([Color.WHITE]), uvs, texture)

static func covers(view: Control, point: Vector2, base: Vector2) -> bool:
	var rect: Rect2 = view.art.registered_rect("backdrop-entrance", base, view.cell)
	var local := (point - rect.position) / rect.size * Vector2(1728, 1344)
	if local.x >= 96 and local.x < 1632 and local.y >= 96 and local.y < ROOF_BOTTOM: return true
	return PANELS.any(func(panel): return Geometry2D.is_point_in_polygon(local, PackedVector2Array(panel)))
