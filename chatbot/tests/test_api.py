"""
Tests for chatbot API endpoints.
"""
from __future__ import annotations

import asyncio
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import AsyncClient, TestCase, override_settings

from chatbot.models import Conversation, Message


class ChatStreamViewTestCase(TestCase):
    """Tests for the ChatStreamView endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = AsyncClient()

    @override_settings(
        OPENAI_API_KEY="test-key",
        OPENAI_DEFAULT_MODEL="gpt-4o-mini",
        ALLOWED_OPENAI_MODELS={"gpt-4o-mini", "gpt-4o", "o1"},
    )
    async def test_stream_response_text_only(self):
        """Test streaming response with text-only input."""
        with patch("chatbot.views.stream_response") as mock_stream:
            # Mock the async generator
            async def mock_gen():
                yield "Hello"
                yield " "
                yield "world"

            mock_stream.return_value = mock_gen()

            response = await self.client.post(
                "/chatbot/api/chat/",
                data={"message": "What is diabetes?", "model": "gpt-4o-mini"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Content-Type"], "text/event-stream")

            # Check that conversation was created
            self.assertEqual(await Conversation.objects.acount(), 1)
            conversation = await Conversation.objects.afirst()
            self.assertEqual(await conversation.messages.acount(), 2)

    @override_settings(
        OPENAI_API_KEY="test-key",
        OPENAI_DEFAULT_MODEL="gpt-4o-mini",
        ALLOWED_OPENAI_MODELS={"gpt-4o-mini", "gpt-4o", "o1"},
    )
    async def test_stream_response_with_image(self):
        """Test streaming response with image upload."""
        with patch("chatbot.views.stream_response") as mock_stream:
            with patch("chatbot.views.to_data_url_if_needed") as mock_image:
                mock_image.return_value = "data:image/png;base64,abc123"

                async def mock_gen():
                    yield "This is a test image."

                mock_stream.return_value = mock_gen()

                # Create a simple image file
                image_data = BytesIO(b"fake-image-data")
                image_file = SimpleUploadedFile(
                    "test.png", image_data.read(), content_type="image/png"
                )

                response = await self.client.post(
                    "/chatbot/api/chat/",
                    data={"message": "What is this?", "files": [image_file]},
                    format="multipart",
                )

                self.assertEqual(response.status_code, 200)

                # Verify image processing was called
                mock_image.assert_called_once()

    @override_settings(
        OPENAI_API_KEY="test-key",
        OPENAI_DEFAULT_MODEL="gpt-4o-mini",
        ALLOWED_OPENAI_MODELS={"gpt-4o-mini", "gpt-4o", "o1"},
    )
    async def test_stream_response_with_pdf(self):
        """Test streaming response with PDF upload."""
        with patch("chatbot.views.stream_response") as mock_stream:
            with patch("chatbot.views.extract_text") as mock_pdf:
                mock_pdf.return_value = "Extracted PDF text content."

                async def mock_gen():
                    yield "Based on the PDF..."

                mock_stream.return_value = mock_gen()

                # Create a fake PDF file
                pdf_data = BytesIO(b"%PDF-1.4 fake-pdf-content")
                pdf_file = SimpleUploadedFile(
                    "test.pdf", pdf_data.read(), content_type="application/pdf"
                )

                response = await self.client.post(
                    "/chatbot/api/chat/",
                    data={"message": "Summarize this document", "files": [pdf_file]},
                    format="multipart",
                )

                self.assertEqual(response.status_code, 200)

                # Verify PDF processing was called
                mock_pdf.assert_called_once()

    @override_settings(
        OPENAI_API_KEY="test-key",
        OPENAI_DEFAULT_MODEL="gpt-4o-mini",
        ALLOWED_OPENAI_MODELS={"gpt-4o-mini"},
    )
    async def test_invalid_model_fallback(self):
        """Test that invalid model falls back to default."""
        with patch("chatbot.views.stream_response") as mock_stream:

            async def mock_gen():
                yield "Response"

            mock_stream.return_value = mock_gen()

            response = await self.client.post(
                "/chatbot/api/chat/",
                data={"message": "Test", "model": "invalid-model"},
            )

            self.assertEqual(response.status_code, 200)

            # Check that default model was used
            call_args = mock_stream.call_args
            self.assertEqual(call_args[1]["model"], "gpt-4o-mini")

    async def test_conversation_persistence(self):
        """Test that conversation history is maintained."""
        # Create a conversation
        convo = await Conversation.objects.acreate()
        await convo.append_user_message("First message")
        await convo.append_assistant_message("First response")

        with patch("chatbot.views.stream_response") as mock_stream:

            async def mock_gen():
                yield "Second response"

            mock_stream.return_value = mock_gen()

            response = await self.client.post(
                "/chatbot/api/chat/",
                data={"message": "Second message", "conversation_id": str(convo.id)},
            )

            self.assertEqual(response.status_code, 200)

            # Verify conversation has 4 messages now
            await convo.arefresh_from_db()
            self.assertEqual(await convo.messages.acount(), 4)


class ConversationModelTestCase(TestCase):
    """Tests for Conversation and Message models."""

    async def test_create_conversation(self):
        """Test creating a conversation."""
        convo = await Conversation.objects.acreate()
        self.assertIsNotNone(convo.id)
        self.assertEqual(convo.message_count, 0)

    async def test_append_messages(self):
        """Test appending messages to a conversation."""
        convo = await Conversation.objects.acreate()

        await convo.append_user_message("Hello")
        await convo.append_assistant_message("Hi there!")

        await convo.arefresh_from_db()
        self.assertEqual(convo.message_count, 2)

        messages = [msg async for msg in convo.messages.all()]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[1].role, "assistant")

    async def test_last_messages(self):
        """Test retrieving last N messages."""
        convo = await Conversation.objects.acreate()

        for i in range(10):
            await convo.append_user_message(f"Message {i}")
            await convo.append_assistant_message(f"Response {i}")

        last_4 = await convo.last_messages(limit=4)
        self.assertEqual(len(last_4), 4)

        # Should be in chronological order
        self.assertIn("Message", last_4[0]["content"])

    @override_settings(CHAT_SUMMARY_AFTER_TURNS=5)
    async def test_auto_summarization(self):
        """Test automatic conversation summarization."""
        with patch("chatbot.models.summarize_conversation") as mock_summarize:
            mock_summarize.return_value = asyncio.coroutine(lambda: "Summary of conversation")()

            convo = await Conversation.objects.acreate()

            # Add enough messages to trigger summarization
            for i in range(6):
                await convo.append_user_message(f"Message {i}")

            await convo.maybe_summarize()

            await convo.arefresh_from_db()
            # Summary should be set
            mock_summarize.assert_called_once()
