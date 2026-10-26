# Independent instant-photo layers

Built-in `image_gen.imagegen` generated **outer paper** and **inner picture frame** separately from the v1 instant-photo material reference, following the user's requested split. Full original outputs are in `raw/`; exact prompts and source/output hashes are alongside them. The v1 original remains historical evidence.

- `raw/outer-paper.png`: blank ivory paper, thickness and lower shadow, with no inset photo window.
- `raw/inner-picture.png`: recessed picture area and narrow inner rim, with no outer paper or caption strip.

Runtime copies are `godot/assets/ui/chef-headshots/photo-outer.png` and `photo-inner.png`. Both use uniform fitting of documented source rectangles; no bitmap is stretched. The paper fits the existing 204×214 logical card. The independently positioned inner frame occupies (22,8,160,142). Its source and content rectangles are recorded in the recipe UI manifest. The same 25:32 chest crop used in recipe headers ends exactly at the inner frame's lower content edge. Names and status stay native in the caption strip.

`raw/assigned-stamp.png` is a separately generated transparent red ink frame. The word **Assigned** is native text centered inside it. Only assigned profiles show the stamp; the caption contains only the chef name, with no Placed/Ready line. Source rectangle (64,120,2048,488) is uniformly fitted to (44,182,116,26), with a -0.04 radian print angle. The exact built-in ImageGen prompt and hashes are preserved in this folder.
