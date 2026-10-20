shader_type canvas_item;
// The catalog's disabled state keeps the generated bevel and highlights while
// replacing warm timber with a subdued slate-blue treatment at draw time.
void fragment() {
	vec4 source = texture(TEXTURE, UV) * COLOR;
	float value = dot(source.rgb, vec3(0.2126, 0.7152, 0.0722));
	COLOR = vec4(vec3(0.10, 0.18, 0.25) + value * vec3(0.34, 0.39, 0.44), source.a);
}
