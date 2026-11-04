#!/usr/bin/env python3
"""Fast tests for the staged phone art budgets; no Godot, SDK or source art."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

import build_android as build


def png(width: int, height: int) -> bytes:
    """A valid one-colour RGBA PNG; the budget gate only reads its header."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\x00" + b"\x00\x00\x00\x00" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class ArtBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        self.image("assets/catalog/sprites/stool/static-S.png", 448, 560)
        self.image("assets/ui/coin.png", 256, 256)
        self.image("assets/expedition/pieces/kelp/idle-S.png", 2304, 1920)

    def tearDown(self):
        self.temporary.cleanup()

    def image(self, relative: str, width: int, height: int) -> None:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png(width, height))

    def test_current_shape_of_payload_passes_and_reports_totals(self):
        report = build.check_art_budgets(self.project)
        self.assertEqual(report["packed_sprite_megapixels"], 0.3)
        self.assertEqual(report["unpacked_tree_megapixels"], {"assets/expedition/pieces": 4.4})
        self.assertEqual(report["largest_images"][0]["path"], "assets/expedition/pieces/kelp/idle-S.png")

    def test_oversized_unpacked_image_is_rejected(self):
        self.image("assets/ui/night-sky.png", 4096, 1024)
        with self.assertRaisesRegex(ValueError, "night-sky.png is 4096x1024"):
            build.check_art_budgets(self.project)

    def test_sprite_folder_outside_the_packer_is_rejected(self):
        self.image("assets/new-feature/sprites/robot/idle-S.png", 64, 64)
        with self.assertRaisesRegex(ValueError, "assets/new-feature/sprites holds sprite atlases"):
            build.check_art_budgets(self.project)

    def test_packed_sprite_total_has_a_budget(self):
        with patch.object(build, "MAX_PACKED_SPRITE_MEGAPIXELS", 0.1):
            with self.assertRaisesRegex(ValueError, "Packed sprites total"):
                build.check_art_budgets(self.project)

    def test_exempt_unpacked_tree_has_its_own_cap(self):
        with patch.dict(build.UNPACKED_TREE_BUDGETS, {"assets/expedition/pieces": 1.0}):
            with self.assertRaisesRegex(ValueError, "assets/expedition/pieces totals 4.4 Mpx"):
                build.check_art_budgets(self.project)

    def test_webp_headers_report_their_size(self):
        extended = b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x0a\x00\x00\x00" + b"\x10\x00\x00\x00" + (1535).to_bytes(3, "little") + (1023).to_bytes(3, "little")
        path = self.project / "assets/ui/exhibition/underwater.webp"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(extended)
        self.assertEqual(build.image_size(path), (1536, 1024))


if __name__ == "__main__":
    unittest.main()
