# Illustrated chef headshots

Current non-scene chef profiles use this coordinated **ImageGen** family, following the user's supplied popup concept. The eight chefs are Lena, Omar, Ama, Mateo, Noor, Dalia, Ellis and Rowan. Existing Blender portraits supply identity/costume references; they remain preserved as historical sources.

## Presentation

- Use these transparent chest-up illustrations in inventory, applications, profiles and recipe headers.
- Recipe headers put the headshot on a separate layer above the rounded popup frame. Its chest meets the header separator and its hat can extend above the popup's top border.
- The dialog uses a shared 25:32 viewport, clipping roughly the bottom 4% of each unchanged 3:4 illustration so the chest rests on the separator. Uniformly scale artwork; do not independently stretch width/height or fit each chef by alpha bounds.
- Keep the popup interior clipped in its own rounded frame. The details surface remains full width with **20px rounded top-left and top-right corners**.
- Existing in-scene sprites, models and projection remain current; this family supplies UI profile artwork.

## Sources

The full unmodified outputs are in `raw/`. Eight exact prompt files, the user's `popup-reference.jpg`, `generation-origins.json` and `provenance.json` preserve the generation record. Built-in `image_gen.imagegen` was used with transparent output; no API/CLI fallback.

Lena establishes the coordinated illustration style. Each subsequent call uses Lena's generated headshot as the style/framing reference, that chef's native front render as an identity reference, and the supplied popup as supporting art direction.

`wireframe/chef-portrait.jsx` and `.css` share the headshots between scenes/components. The HTML wood dock's People inventory uses the same illustrated files. Open `#chef-ui-portraits` to review the full family and dialog crops.
