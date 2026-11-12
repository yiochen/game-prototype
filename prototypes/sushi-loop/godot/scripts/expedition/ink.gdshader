shader_type canvas_item;
// Issue #70 Inkfin ink: a full-view layer over the dive (above the creature,
// below the cable and the steering arrows). Ink covers the sea; the ship's
// light cone, with a curved front, cuts through it and shows what it reaches
// in purple monochrome. Lengths are in view units; `cell` is one column.

uniform sampler2D screen_texture : hint_screen_texture, filter_linear;
uniform vec2 view_size = vec2(390.0, 844.0);
uniform float cell = 55.0;
uniform vec2 ship = vec2(195.0, 620.0);
uniform vec2 origin = vec2(195.0, 300.0);     // where the ink leaves the cuttlefish
uniform vec2 scroll = vec2(0.0);              // world origin, so the billows ride the terrain
uniform float cover = 0.0;                    // 0 clear .. 1 full
uniform float bloom = 0.0;                    // 1 while the ink is still seeping out from `origin`
uniform float warn = 0.0;                     // purple edge pulse before the ink
uniform float tilt = 0.0;                     // radians, positive swings the beam right
uniform float clear_rows = 3.0;
uniform float far_half_columns = 2.5;
uniform float glow_columns = 0.9;
uniform float darkness = 0.92;
uniform float tint = 1.0;
uniform float drift = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float billow(vec2 p) { return 0.55 * noise(p) + 0.3 * noise(p * 2.1 + 7.3) + 0.15 * noise(p * 4.3 + 2.9); }

void fragment() {
	vec2 p = UV * view_size;
	vec3 scene = texture(screen_texture, SCREEN_UV).rgb;

	// Ink here: seeping out from the cuttlefish with a soft front, then everywhere.
	float ink = cover;
	if (bloom > 0.5) {
		float reach = max(1.0, cover * length(view_size) * 1.6);
		ink = 1.0 - smoothstep(0.55 * reach, reach, distance(p, origin));
	}

	// The light: a forward cone whose front is an arc round the ship, plus a glow round the hull.
	vec2 d = p - ship;
	vec2 q = vec2(cos(tilt) * d.x + sin(tilt) * d.y, -sin(tilt) * d.x + cos(tilt) * d.y);
	float ahead = -q.y;
	float reach_px = clear_rows * cell;
	float fade = 0.9 * cell;
	float soft = 0.14 * cell;
	float half_width = glow_columns * cell + (far_half_columns - glow_columns) * cell * ahead / reach_px;
	float cone = (1.0 - smoothstep(reach_px, reach_px + fade, length(q)))
		* (1.0 - smoothstep(half_width - soft, half_width + soft, abs(q.x)))
		* smoothstep(-0.2 * cell - soft, -0.2 * cell + soft, ahead);
	float hull = glow_columns * cell * 1.45;
	float glow = 1.0 - smoothstep(0.55 * hull, hull, distance(p, ship - vec2(0.0, 0.1 * cell)));
	float light = max(cone, glow);

	// What the light shows keeps its brightness but takes the purple's hue (grayscale, in purple).
	const vec3 weights = vec3(0.299, 0.587, 0.114);
	const vec3 purple = vec3(0.588, 0.373, 0.843);
	float lum = dot(scene, weights);
	vec3 mono = purple + (lum - dot(purple, weights));
	float low = min(mono.r, min(mono.g, mono.b));
	float high = max(mono.r, max(mono.g, mono.b));
	if (low < 0.0) mono = lum + (mono - lum) * lum / (lum - low);
	if (high > 1.0) mono = lum + (mono - lum) * (1.0 - lum) / (high - lum);
	vec3 lit = mix(scene, mono, tint * cover);

	// Billowing ink, darker in the middle of each cloud.
	vec2 cloud_at = (p - scroll) / (cell * 4.5) + vec2(drift, 0.0);
	float cloud = billow(cloud_at);
	vec3 ink_color = mix(vec3(0.024, 0.008, 0.055), vec3(0.24, 0.09, 0.42), smoothstep(0.35, 0.75, cloud) * 0.6);
	// `darkness` is the thinnest the ink gets; the billows are thicker still.
	float alpha = (1.0 - (1.0 - darkness) * (1.0 - 0.85 * smoothstep(0.25, 0.65, cloud))) * ink * (1.0 - light);
	vec3 color = mix(lit, ink_color, alpha);

	// Warning: the edges pulse purple while the whole sea is still in view.
	float edge = smoothstep(0.25 * view_size.y, 0.75 * view_size.y, distance(p, view_size * 0.5));
	color = mix(color, vec3(0.157, 0.039, 0.275), warn * edge);
	COLOR = vec4(color, 1.0);
}
