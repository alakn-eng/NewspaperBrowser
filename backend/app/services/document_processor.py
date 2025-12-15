"""
Document processor service for converting PDFs to images.

Uses pdf2image to convert PDF pages into individual PNG images.
"""

from typing import List, Protocol
from io import BytesIO

from pdf2image import convert_from_bytes
from PIL import Image


class DocumentProcessor(Protocol):
    """Protocol for document processing services."""

    def process(self, file_bytes: bytes) -> List[bytes]:
        """
        Convert document to list of page images.

        Args:
            file_bytes: Raw document bytes (PDF)

        Returns:
            List of image bytes (one per page), in PNG format
        """
        ...


class PdfDocumentProcessor:
    """
    PDF document processor using pdf2image.

    Converts PDF files into individual page images (PNG format).
    """

    def __init__(self, dpi: int = 300, image_format: str = "PNG"):
        """
        Initialize PDF document processor.

        Args:
            dpi: Resolution for image conversion (default 300)
            image_format: Output image format (default PNG)
        """
        self.dpi = dpi
        self.image_format = image_format

    def process(self, file_bytes: bytes) -> List[bytes]:
        """
        Convert PDF to list of page images.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            List of image bytes (one per page), in PNG format

        Raises:
            Exception: If PDF conversion fails
        """
        try:
            # Convert PDF bytes to list of PIL Images
            images = convert_from_bytes(
                file_bytes,
                dpi=self.dpi,
                fmt=self.image_format.lower(),
            )

            # Convert PIL Images to bytes
            page_images = []
            for image in images:
                image_buffer = BytesIO()
                image.save(image_buffer, format=self.image_format)
                image_buffer.seek(0)
                page_images.append(image_buffer.getvalue())

            return page_images

        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}") from e


# Factory function for dependency injection
def get_document_processor() -> PdfDocumentProcessor:
    """
    Get document processor instance.

    Returns:
        PdfDocumentProcessor configured with default settings
    """
    return PdfDocumentProcessor(dpi=300, image_format="PNG")
