shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;
uniform sampler2D native_layer : filter_nearest, repeat_disable;
uniform sampler2D mip_1 : filter_nearest, repeat_disable;
uniform sampler2D mip_2 : filter_nearest, repeat_disable;
uniform sampler2D mip_3 : filter_nearest, repeat_disable;
uniform sampler2D mip_4 : filter_nearest, repeat_disable;

varying vec4 vertex_tint;
void vertex() { vertex_tint = COLOR; }

vec4 level_texel(int level, ivec2 pixel) {
	if (level == 4) { return texelFetch(mip_4, pixel, 0); }
	if (level == 3) { return texelFetch(mip_3, pixel, 0); }
	if (level == 2) { return texelFetch(mip_2, pixel, 0); }
	if (level == 1) { return texelFetch(mip_1, pixel, 0); }
	return texelFetch(native_layer, pixel, 0);
}

void fragment() {
	vec2 base_size = vec2(textureSize(native_layer, 0));
	vec2 native_footprint = fwidth(UV) * base_size;
	float span = max(native_footprint.x, native_footprint.y);
	// Stable at exact2x/4x/8x: numerical2.0000002 must not become an equal3-tap average.
	int level = int(clamp(floor(log2(max(span, 1.0)) + 0.000001), 0.0, 4.0));
	vec2 dimensions = base_size / exp2(float(level));
	vec2 footprint = max(native_footprint / exp2(float(level)), vec2(1.0));
	vec2 low = UV * dimensions - footprint * 0.5;
	vec2 high = low + footprint;
	ivec2 first = ivec2(floor(low + vec2(0.000001)));
	vec4 value = vec4(0.0);
	// The chosen reduction level leaves a <=2x footprint. Weight exact texel
	// intersections rather than choosing a sample count from floating ceil().
	for (int y = 0; y < 3; y++) {
		for (int x = 0; x < 3; x++) {
			ivec2 pixel = first + ivec2(x, y);
			vec2 p = vec2(pixel);
			vec2 overlap = max(vec2(0.0), min(high, p + vec2(1.0)) - max(low, p));
			if (pixel.x >= 0 && pixel.y >= 0 && pixel.x < int(dimensions.x) && pixel.y < int(dimensions.y)) {
				value += level_texel(level, pixel) * overlap.x * overlap.y;
			}
		}
	}
	COLOR = value / (footprint.x * footprint.y);
	COLOR *= vec4(vertex_tint.rgb * vertex_tint.a, vertex_tint.a);
}
