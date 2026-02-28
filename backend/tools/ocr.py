"""OCR tool — extract text from images using pytesseract as fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class OCRTool:
    """Extract text from images using OCR.

    Primary: pytesseract (Tesseract OCR).
    This is a fallback tool for scanned PDFs or image-based documents.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}

    def extract_text(
        self,
        file_path: str,
        *,
        lang: str = "eng",
    ) -> str:
        """Extract text from an image file using OCR.

        Args:
            file_path: Path to the image file.
            lang: Tesseract language code (e.g. "eng", "deu", "fra").

        Returns:
            Extracted text string.

        Raises:
            ValueError: If file extension is not supported.
            ImportError: If pytesseract is not installed.
        """
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image type: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "pytesseract and Pillow are required for OCR. "
                "Install with: pip install pytesseract Pillow"
            ) from e

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()

    def is_available(self) -> bool:
        """Check if OCR dependencies are installed and Tesseract is accessible."""
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
