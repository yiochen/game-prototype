shader_type canvas_item;
uniform vec2 surface_size = vec2(332.0, 221.3333);
uniform float corner_radius = 16.0;

void fragment() {
	vec2 p = UV * surface_size;
	vec2 q = abs(p - surface_size * 0.5) - surface_size * 0.5 + vec2(corner_radius);
	float distance_to_edge = length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - corner_radius;
	float edge = max(fwidth(distance_to_edge), 0.001);
	vec4 image = texture(TEXTURE, UV);
	COLOR = vec4(image.rgb, image.a * (1.0 - smoothstep(-edge, edge, distance_to_edge)));
}
