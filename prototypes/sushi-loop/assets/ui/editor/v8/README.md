# Restore the approved cloth curtains

No new artwork was generated. The active and idle curtain entries reuse the exact v6 source rectangles, pixels and corner calibration. Their measured visible faces retain native icon/text alignment, and Godot lowers the cloth slightly so the original straps meet the rod.

The three v6 generation receipts and complete-screen composition remain pinned. The v7 open-ring study is preserved in its own directory as history and is not in this runtime atlas. Other v7 UI measurements/materials remain, including bare chevrons, compact goods and the thicker dock. A full-width beige backdrop is composed in Godot independently from the narrow goods drawer. The rod uses calibrated overscan so its visible wood reaches both screen edges.

Run `pack.py` with Pillow to reproduce the atlas. Crops are packed unchanged with four transparent sampling pixels; nothing is repainted or resized.
