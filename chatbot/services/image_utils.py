"""
Image processing utilities for converting images to data URLs.

Supports various image formats and converts them to base64 data URLs
for use with OpenAI's Vision API.
"""
from __future__ import annotations

import base64
import io

from django.core.files.uploadedfile import UploadedFile

try:
    from PIL import Image

    PILLOW_SUPPORT = True
except ImportError:
    PILLOW_SUPPORT = False


def to_data_url(image_file: UploadedFile, max_size: tuple[int, int] = (2048, 2048)) -> str:
    """
    Convert an uploaded image to a base64 data URL.

    Args:
        image_file: Uploaded image file.
        max_size: Maximum dimensions (width, height) to resize to.

    Returns:
        Base64 data URL string (e.g., data:image/png;base64,...)
    """
    if not PILLOW_SUPPORT:
        return ""

    try:
        image_file.seek(0)
        img = Image.open(image_file)

        # Convert RGBA to RGB if needed
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = background

        # Resize if too large
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convert to base64
        buffer = io.BytesIO()
        img_format = img.format or "PNG"
        img.save(buffer, format=img_format)
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Determine MIME type
        mime_type = f"image/{img_format.lower()}"
        if img_format.upper() == "JPEG":
            mime_type = "image/jpeg"

        return f"data:{mime_type};base64,{img_b64}"

    except Exception as e:
        return ""


def to_data_url_if_needed(image_file: UploadedFile) -> str:
    """
    Convert image to data URL if it's a valid image file.

    Args:
        image_file: Uploaded file.

    Returns:
        Data URL string or empty string on error.
    """
    return to_data_url(image_file)
