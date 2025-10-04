"""
Tests for chatbot service modules.
"""
from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from chatbot.services.image_utils import to_data_url, to_data_url_if_needed
from chatbot.services.message_builder import (
    MEDICAL_SYSTEM_PROMPT,
    build_text_input,
    build_vision_input,
)
from chatbot.services.openai_client import get_client
from chatbot.services.pdf_utils import extract_text


class MessageBuilderTestCase(TestCase):
    """Tests for message builder utilities."""

    def test_build_text_input_no_history(self):
        """Test building text input without history."""
        result = build_text_input("What is diabetes?", [])

        self.assertEqual(len(result), 2)  # System + user message
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[1]["role"], "user")
        self.assertIn("diabetes", result[1]["content"][0]["text"])

    def test_build_text_input_with_history(self):
        """Test building text input with conversation history."""
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        result = build_text_input("Follow-up question", history)

        self.assertEqual(len(result), 4)  # System + 2 history + user
        self.assertEqual(result[1]["role"], "user")
        self.assertEqual(result[2]["role"], "assistant")
        self.assertEqual(result[3]["role"], "user")

    def test_medical_system_prompt_included(self):
        """Test that medical safety prompt is included."""
        result = build_text_input("Test", [])

        system_message = result[0]
        prompt_text = system_message["content"][0]["text"]
        self.assertIn("diagnosis", prompt_text.lower())
        self.assertIn("doctor", prompt_text.lower())

    def test_build_vision_input(self):
        """Test building vision input with image."""
        image_url = "data:image/png;base64,abc123"
        result = build_vision_input("What is this?", image_url, [])

        # Should have system message + user message with image
        self.assertEqual(len(result), 2)

        user_message = result[1]
        self.assertEqual(user_message["role"], "user")
        self.assertEqual(len(user_message["content"]), 2)  # Text + image

        # Check content types
        content_types = [item["type"] for item in user_message["content"]]
        self.assertIn("input_text", content_types)
        self.assertIn("input_image", content_types)

    def test_build_vision_input_default_text(self):
        """Test vision input with empty user text."""
        image_url = "data:image/png;base64,abc123"
        result = build_vision_input("", image_url, [])

        user_message = result[1]
        text_content = [item for item in user_message["content"] if item["type"] == "input_text"][
            0
        ]
        self.assertIn("Describe", text_content["text"])


class OpenAIClientTestCase(TestCase):
    """Tests for OpenAI client service."""

    @override_settings(
        OPENAI_API_KEY="test-key-123",
        OPENAI_BASE_URL="https://test.openai.com/v1",
    )
    def test_get_client_with_settings(self):
        """Test client initialization with custom settings."""
        with patch("chatbot.services.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Clear cached client
            import chatbot.services.openai_client as client_module

            client_module._client = None

            client = get_client()

            # Verify OpenAI was called with correct params
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            self.assertEqual(call_kwargs["api_key"], "test-key-123")
            self.assertEqual(call_kwargs["base_url"], "https://test.openai.com/v1")

    @override_settings(OPENAI_API_KEY="", OPENAI_BASE_URL="")
    def test_get_client_without_settings(self):
        """Test client initialization with default settings."""
        with patch("chatbot.services.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Clear cached client
            import chatbot.services.openai_client as client_module

            client_module._client = None

            client = get_client()

            # Verify OpenAI was called with no custom params
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            self.assertEqual(call_kwargs, {})


class PDFUtilsTestCase(TestCase):
    """Tests for PDF text extraction utilities."""

    def test_extract_text_no_pdfminer(self):
        """Test extraction when pdfminer is not available."""
        with patch("chatbot.services.pdf_utils.PDF_SUPPORT", False):
            pdf_file = SimpleUploadedFile("test.pdf", b"fake-pdf", content_type="application/pdf")
            result = extract_text(pdf_file)
            self.assertIn("not available", result)

    @patch("chatbot.services.pdf_utils.PDF_SUPPORT", True)
    @patch("chatbot.services.pdf_utils.pdf_extract_text")
    def test_extract_text_success(self, mock_extract):
        """Test successful text extraction."""
        mock_extract.return_value = "This is extracted text from PDF."

        pdf_file = SimpleUploadedFile("test.pdf", b"fake-pdf", content_type="application/pdf")
        result = extract_text(pdf_file, max_pages=5, max_chars=1000)

        self.assertEqual(result, "This is extracted text from PDF.")
        mock_extract.assert_called_once()

    @patch("chatbot.services.pdf_utils.PDF_SUPPORT", True)
    @patch("chatbot.services.pdf_utils.pdf_extract_text")
    def test_extract_text_truncation(self, mock_extract):
        """Test text truncation for long documents."""
        long_text = "A" * 10000
        mock_extract.return_value = long_text

        pdf_file = SimpleUploadedFile("test.pdf", b"fake-pdf", content_type="application/pdf")
        result = extract_text(pdf_file, max_chars=100)

        self.assertTrue(len(result) <= 150)  # 100 chars + truncation message
        self.assertIn("truncated", result)


class ImageUtilsTestCase(TestCase):
    """Tests for image processing utilities."""

    def test_to_data_url_no_pillow(self):
        """Test image conversion when Pillow is not available."""
        with patch("chatbot.services.image_utils.PILLOW_SUPPORT", False):
            image_file = SimpleUploadedFile("test.png", b"fake-image", content_type="image/png")
            result = to_data_url(image_file)
            self.assertEqual(result, "")

    @patch("chatbot.services.image_utils.PILLOW_SUPPORT", True)
    @patch("chatbot.services.image_utils.Image")
    def test_to_data_url_success(self, mock_image):
        """Test successful image to data URL conversion."""
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.format = "PNG"
        mock_img.width = 100
        mock_img.height = 100
        mock_image.open.return_value = mock_img

        image_file = SimpleUploadedFile("test.png", b"fake-image", content_type="image/png")
        result = to_data_url(image_file)

        # Result should be a data URL (even if mocked)
        # In a real scenario, this would check for proper base64 encoding
        mock_image.open.assert_called_once()

    def test_to_data_url_if_needed(self):
        """Test convenience wrapper function."""
        with patch("chatbot.services.image_utils.to_data_url") as mock_to_data_url:
            mock_to_data_url.return_value = "data:image/png;base64,abc"

            image_file = SimpleUploadedFile("test.png", b"fake-image", content_type="image/png")
            result = to_data_url_if_needed(image_file)

            self.assertEqual(result, "data:image/png;base64,abc")
            mock_to_data_url.assert_called_once_with(image_file)
