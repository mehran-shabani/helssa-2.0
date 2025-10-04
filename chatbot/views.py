"""
Chatbot views for handling async streaming chat requests.

Provides HTTP endpoints for real-time streaming chat using Server-Sent Events (SSE).
"""
from __future__ import annotations

import asyncio
import json
import logging

from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from chatbot.models import Conversation
from chatbot.services.image_utils import to_data_url_if_needed
from chatbot.services.message_builder import build_text_input, build_vision_input
from chatbot.services.openai_client import stream_response
from chatbot.services.pdf_utils import extract_text

logger = logging.getLogger(__name__)


def index(request):
    """Render the chatbot interface."""
    return render(request, "chatbot/index.html")


@method_decorator(csrf_exempt, name="dispatch")
class ChatStreamView(View):
    """
    Async view for streaming chat responses via Server-Sent Events.

    Accepts:
        - message: User's text message
        - model: Optional model name (must be in ALLOWED_OPENAI_MODELS)
        - conversation_id: Optional conversation UUID for continuity
        - files: Optional uploaded files (images or PDFs)

    Returns:
        StreamingHttpResponse with SSE events containing response deltas.
    """

    async def post(self, request):
        """Handle POST request for streaming chat."""
        try:
            # Extract request parameters
            user_text = request.POST.get("message", "").strip()
            model = request.POST.get("model") or settings.OPENAI_DEFAULT_MODEL

            # Validate model
            if model not in settings.ALLOWED_OPENAI_MODELS:
                logger.warning(f"Invalid model requested: {model}, using default")
                model = settings.OPENAI_DEFAULT_MODEL

            # Get or create conversation
            conversation_id = request.POST.get("conversation_id")
            convo = await Conversation.aget_or_create_default(conversation_id)

            # Get conversation history
            history = await convo.last_messages(limit=settings.CHAT_MAX_HISTORY_TURNS)

            # Process uploaded files
            files = request.FILES.getlist("files")
            image_data_url = None

            for f in files:
                content_type = f.content_type or ""

                if content_type == "application/pdf":
                    # Extract text from PDF
                    pdf_text = await asyncio.to_thread(
                        extract_text, f, max_pages=8, max_chars=8000
                    )
                    user_text += f"\n\n[PDF extract (truncated)]:\n{pdf_text}"

                elif content_type.startswith("image/"):
                    # Convert image to data URL for Vision API
                    image_data_url = await asyncio.to_thread(to_data_url_if_needed, f)

            # Build input payload
            if image_data_url:
                input_payload = build_vision_input(user_text, image_data_url, history)
            else:
                input_payload = build_text_input(user_text, history)

            # Stream response
            async def event_stream():
                """Generate SSE stream with response deltas."""
                try:
                    # Save user message
                    await convo.append_user_message(user_text)

                    # Send conversation ID to client
                    yield f"event: conversation\ndata: {json.dumps({'id': str(convo.id)})}\n\n"

                    # Collect assistant response
                    assistant_text = ""

                    # Stream response from OpenAI
                    async for chunk in stream_response(
                        model=model,
                        input_payload=input_payload,
                        temperature=0.4,
                        timeout=settings.OPENAI_TIMEOUT,
                    ):
                        assistant_text += chunk
                        yield f"data: {json.dumps({'delta': chunk})}\n\n"

                    # Save assistant message
                    await convo.append_assistant_message(assistant_text)

                    # Check if summarization is needed
                    await convo.maybe_summarize()

                    # Send completion event
                    yield "event: done\ndata: [DONE]\n\n"

                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}", exc_info=True)
                    error_msg = f"Error: {str(e)}"
                    yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"

            return StreamingHttpResponse(
                event_stream(),
                content_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        except Exception as e:
            logger.error(f"Error in ChatStreamView: {str(e)}", exc_info=True)
            return StreamingHttpResponse(
                iter([f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"]),
                content_type="text/event-stream",
                status=500,
            )
