"""Regression tests for bounded PDF-to-image conversion."""

import unittest
from unittest.mock import patch

from core.media import PDFExtractor, _MAX_PDF_IMAGE_PAGES


class TestPdfImageOutputBounds(unittest.TestCase):
    def test_to_images_rejects_excessive_page_requests_before_converter_runs(self):
        extractor = PDFExtractor()
        extractor._bin_pdftoppm = "pdftoppm"
        requested_pages = list(range(1, _MAX_PDF_IMAGE_PAGES + 2))

        with patch("core.media._run") as command:
            with self.assertRaisesRegex(ValueError, "page limit"):
                extractor.to_images(b"%PDF-1.4", pages=requested_pages)

        command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
