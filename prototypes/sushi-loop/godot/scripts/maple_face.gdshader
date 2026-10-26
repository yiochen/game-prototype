shader_type canvas_item;
uniform vec2 surface_size = vec2(672.0, 1100.0);
uniform float corner_radius = 32.0;
uniform float grain_width = 720.0;

void fragment() {
	vec2 p = UV * surface_size;
	vec2 q = abs(p - surface_size * 0.5) - surface_size * 0.5 + vec2(corner_radius);
	float distance_to_edge = length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - corner_radius;
	float edge = max(fwidth(distance_to_edge), 0.001);
	float coverage = 1.0 - smoothstep(-edge, edge, distance_to_edge);
	vec2 grain_size = vec2(grain_width, grain_width * TEXTURE_PIXEL_SIZE.x / TEXTURE_PIXEL_SIZE.y);
	vec4 grain = texture(TEXTURE, p / grain_size);
	COLOR = vec4(mix(grain.rgb, vec3(1.0, 0.886, 0.686), 0.12), grain.a * coverage);
}
