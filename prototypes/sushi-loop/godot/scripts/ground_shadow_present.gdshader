shader_type canvas_item;
render_mode unshaded;

void fragment() {
	float shadow = 1.0 - texture(TEXTURE, UV).r;
	COLOR = vec4(0.20, 0.14, 0.10, clamp(shadow, 0.0, 1.0) * 0.18);
}
