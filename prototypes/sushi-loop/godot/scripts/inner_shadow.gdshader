shader_type canvas_item;
// CSS `box-shadow: inset <offset> <blur> <color>` on a rounded rect: the shadow
// falls inside the surface from the edges the offset points away from.
uniform vec2 rect_size = vec2(100.0);
uniform float radius = 0.0;
uniform vec2 offset = vec2(0.0, 2.0);
uniform float blur = 4.0;
uniform vec4 shadow_color : source_color = vec4(0.5, 0.33, 0.18, 0.14);

float rounded(vec2 p, vec2 half_size, float r) {
	vec2 q = abs(p) - half_size + r;
	return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void fragment() {
	vec2 p = UV * rect_size - rect_size * 0.5;
	float r = min(radius, min(rect_size.x, rect_size.y) * 0.5);
	float inside = 1.0 - smoothstep(-1.0, 0.0, rounded(p, rect_size * 0.5, r));
	float shade = smoothstep(-blur, blur * 0.5, rounded(p - offset, rect_size * 0.5, r));
	COLOR = vec4(shadow_color.rgb, shadow_color.a * shade * inside);
}
