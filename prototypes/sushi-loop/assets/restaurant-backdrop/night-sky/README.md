# Night-sky camera-clearance strip

Generated with the built-in `image_gen.imagegen` tool. [Exact prompt and provenance](generation.json). The complete original output is `night-sky-original.png`; `godot/assets/ui/night-sky.png` is an identical copy. The renderer uniformly scales and crops the sky above the roof, preserving the original aspect ratio.

A minimum 80 logical units at a 720-unit scene width leaves a quiet top strip. Device-reported safe area and camera cutouts enlarge it when needed, with 12 logical units of clearance. Coins, Editing, Live and Shop begin below the strip; the HUD can overlap the shingles. The sky stays fixed while the restaurant pans.
