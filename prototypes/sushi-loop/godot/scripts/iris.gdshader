shader_type canvas_item;
// #28 scene transition: navy everywhere outside a circular hole, with a cream rim.
uniform vec2 centre;
uniform float radius;
uniform float rim_width = 5.0;
uniform vec4 navy : source_color = vec4(0.059, 0.141, 0.2, 1.0);
uniform vec4 rim : source_color = vec4(1.0, 0.945, 0.827, 1.0);
varying vec2 local;
void vertex() { local = VERTEX; }
void fragment() {
	float d = distance(local, centre);
	float outside = smoothstep(radius - 1.0, radius + 1.0, d);
	float edge = 1.0 - smoothstep(rim_width * 0.5 - 1.0, rim_width * 0.5 + 1.0, abs(d - radius));
	vec4 color = mix(vec4(navy.rgb, outside), rim, edge * step(2.0, radius));
	COLOR = color;
}
