extends RefCounted
## Convert the mobile display's physical camera clearance into canvas units.

static func top_inset(safe_area: Rect2, cutouts: Array, transform: Transform2D, display_height: float) -> float:
	var physical_top := maxf(0.0, safe_area.position.y)
	for cutout: Rect2 in cutouts:
		# Only top cameras/notches contribute; bottom and side hardware do not
		# turn the entire screen into a header.
		if cutout.has_area() and cutout.end.y <= display_height * 0.5:
			physical_top = maxf(physical_top, cutout.end.y)
	return maxf(0.0, (transform.affine_inverse() * Vector2(0, physical_top)).y)
