# Native 135% contrast verification

User preference: **135% looks best**. The live review now starts at that grade, and the new native proof compares an sRGB compositor grade with the browser display grade for four objects × four facings. The source project, exact node recipe and method are in [the native asset folder](../../../assets/native-contrast/README.md).

16 original/native render pairs pass the audit: original controls exactly match existing sprite pixels; alpha is byte-identical; native opaque RGB differs from the browser formula by less than 0.42 channel units on average and at most 1.125 units. Graph inspection verifies original-alpha bypass, three clamped Multiply Add operations, forward/back sRGB conversions and zero lights/world illumination. No directional capture lighting was added.

164 engine tests, production build and three responsive browser checks pass. The browser tests cover both scene sets, default 135%, all facing choices, matching viewBoxes, native source/download URLs and an unfiltered baked-image display, alongside existing reference/projection/grid/repetition/single-scroll checks. Screenshots show the native and browser sides at phone, landscape and desktop widths.

135% is a selected color direction. Geometry, final scene-asset approval and production rollout remain separate; issue 33 stays open.
