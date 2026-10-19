# Noor lighting study review

The isolated lighting experiment is available at `#character-lighting-study` in
Scene art review, with a link from Noor's production object page. It compares
the current emission baseline with Soft, Faceted and Crisp overhead treatments.
No treatment is selected and production sprites remain unchanged.

All sixteen native stills share the same 192×320 logical frame, root (96,248),
128-pixel square tile and 4× source resolution. The facing selector exposes
South, East, North and West for every candidate. Enlarged hat views use the
same logical crop (27,65,137,95), directly from the native image. The browser
does not apply image filters. The original restaurant concept remains available
unchanged below the comparison.

Validation:

- 183 engine tests passed.
- Production build passed.
- Three responsive browser cases passed at 390×844, 844×390 and 1440×1000.
- Browser checks inspect all sixteen PNGs, matching capture registration and
  display scale,4× image dimensions, hat crops, facing changes, source links,
  the original reference and one document scrollbar.
- `git diff --check` passed.

The phone and desktop comparison screenshots were visually inspected: the
candidate hat tops are clearly brighter than their sides, each treatment keeps
the face readable, and four matched captures share aligned tile roots. The
two-column phone layout and four-column wider layout preserve the same view and
crop across treatments.

`engine.log`, `build.log` and `browser.log` preserve validation output.
`character-lighting-390.png`, `character-lighting-844.png` and
`character-lighting-1440.png` preserve the final responsive comparison.
