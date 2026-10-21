shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;
// ViewportTexture already contains premultiplied RGB. A linear sample exactly
// between four native texel centres is the 2x2 area mean; never multiply alpha again.
void fragment() {
	COLOR = textureLod(TEXTURE, UV, 0.0);
}
