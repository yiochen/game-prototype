shader_type spatial;
render_mode ambient_light_disabled, specular_disabled, cull_disabled;

void fragment() {
	ALBEDO = vec3(1.0);
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}

// Native shadow-map attenuation only. Lighting/contrast on the color sprites
// stays in their approved artwork, independent of this white floor receiver.
void light() {
	DIFFUSE_LIGHT += vec3(ATTENUATION);
}
