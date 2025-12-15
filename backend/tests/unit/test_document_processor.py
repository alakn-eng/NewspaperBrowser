"""
Unit tests for document processor service.

Tests PDF to image conversion using pdf2image.
"""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from app.services.document_processor import PdfDocumentProcessor, get_document_processor


@pytest.fixture
def sample_pdf_bytes():
    """
    Create a minimal valid PDF for testing.

    This creates a simple single-page PDF programmatically.
    """
    # Minimal PDF structure (1 page, blank)
    # This is a valid PDF header + basic structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Page) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000315 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
407
%%EOF
"""
    return pdf_content


@pytest.fixture
def mock_pil_images():
    """Create mock PIL Images for testing."""
    # Create simple test images
    image1 = Image.new("RGB", (100, 100), color="red")
    image2 = Image.new("RGB", (100, 100), color="blue")
    return [image1, image2]


class TestPdfDocumentProcessor:
    """Test PDF document processor."""

    def test_initialization(self):
        """Test processor initialization with custom settings."""
        processor = PdfDocumentProcessor(dpi=150, image_format="JPEG")

        assert processor.dpi == 150
        assert processor.image_format == "JPEG"

    def test_initialization_defaults(self):
        """Test processor initialization with default settings."""
        processor = PdfDocumentProcessor()

        assert processor.dpi == 300
        assert processor.image_format == "PNG"

    @patch("app.services.document_processor.convert_from_bytes")
    def test_process_single_page_pdf(self, mock_convert, sample_pdf_bytes):
        """Test processing a single-page PDF."""
        # Create a mock PIL Image
        mock_image = Image.new("RGB", (100, 100), color="white")
        mock_convert.return_value = [mock_image]

        processor = PdfDocumentProcessor()
        result = processor.process(sample_pdf_bytes)

        # Verify convert_from_bytes was called correctly
        mock_convert.assert_called_once_with(
            sample_pdf_bytes,
            dpi=300,
            fmt="png",
        )

        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], bytes)
        assert len(result[0]) > 0

    @patch("app.services.document_processor.convert_from_bytes")
    def test_process_multi_page_pdf(self, mock_convert, sample_pdf_bytes, mock_pil_images):
        """Test processing a multi-page PDF."""
        mock_convert.return_value = mock_pil_images

        processor = PdfDocumentProcessor()
        result = processor.process(sample_pdf_bytes)

        # Verify result has correct number of pages
        assert len(result) == 2
        assert all(isinstance(page_bytes, bytes) for page_bytes in result)
        assert all(len(page_bytes) > 0 for page_bytes in result)

    @patch("app.services.document_processor.convert_from_bytes")
    def test_process_with_custom_dpi(self, mock_convert, sample_pdf_bytes):
        """Test processing with custom DPI setting."""
        mock_image = Image.new("RGB", (200, 200), color="white")
        mock_convert.return_value = [mock_image]

        processor = PdfDocumentProcessor(dpi=150)
        result = processor.process(sample_pdf_bytes)

        # Verify DPI was passed correctly
        mock_convert.assert_called_once_with(
            sample_pdf_bytes,
            dpi=150,
            fmt="png",
        )

        assert len(result) == 1

    @patch("app.services.document_processor.convert_from_bytes")
    def test_process_with_jpeg_format(self, mock_convert, sample_pdf_bytes):
        """Test processing with JPEG output format."""
        mock_image = Image.new("RGB", (100, 100), color="white")
        mock_convert.return_value = [mock_image]

        processor = PdfDocumentProcessor(image_format="JPEG")
        result = processor.process(sample_pdf_bytes)

        # Verify format was passed correctly
        mock_convert.assert_called_once_with(
            sample_pdf_bytes,
            dpi=300,
            fmt="jpeg",
        )

        assert len(result) == 1

    @patch("app.services.document_processor.convert_from_bytes")
    def test_process_invalid_pdf(self, mock_convert):
        """Test processing invalid PDF raises exception."""
        mock_convert.side_effect = Exception("Invalid PDF")

        processor = PdfDocumentProcessor()

        with pytest.raises(Exception) as exc_info:
            processor.process(b"invalid pdf content")

        assert "Failed to process PDF" in str(exc_info.value)

    @patch("app.services.document_processor.convert_from_bytes")
    def test_image_bytes_are_valid_png(self, mock_convert, sample_pdf_bytes):
        """Test that returned bytes are valid PNG images."""
        mock_image = Image.new("RGB", (100, 100), color="green")
        mock_convert.return_value = [mock_image]

        processor = PdfDocumentProcessor()
        result = processor.process(sample_pdf_bytes)

        # Verify the bytes can be loaded as a PNG image
        image_from_bytes = Image.open(BytesIO(result[0]))
        assert image_from_bytes.format == "PNG"
        assert image_from_bytes.size == (100, 100)


class TestFactoryFunction:
    """Test factory function for dependency injection."""

    def test_get_document_processor(self):
        """Test factory function returns configured processor."""
        processor = get_document_processor()

        assert isinstance(processor, PdfDocumentProcessor)
        assert processor.dpi == 300
        assert processor.image_format == "PNG"


class TestIntegrationWithRealPdf:
    """
    Integration tests with actual PDF processing.

    These tests use the real pdf2image library with a minimal PDF.
    """

    def test_process_minimal_pdf(self, sample_pdf_bytes):
        """Test processing a real minimal PDF."""
        processor = PdfDocumentProcessor(dpi=72)  # Lower DPI for faster test

        try:
            result = processor.process(sample_pdf_bytes)

            # Verify we got image bytes back
            assert len(result) == 1
            assert isinstance(result[0], bytes)

            # Verify the bytes are a valid image
            image = Image.open(BytesIO(result[0]))
            assert image.format == "PNG"
            assert image.size[0] > 0
            assert image.size[1] > 0

        except Exception as e:
            # If poppler is not installed, skip this test
            if "poppler" in str(e).lower():
                pytest.skip("Poppler not installed - skipping real PDF test")
            else:
                raise
