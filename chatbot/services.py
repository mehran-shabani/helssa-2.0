from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class ChatbotAdapter(ABC):
    @abstractmethod
    def reply(self, message: str, *, context: Mapping[str, Any] | None = None) -> str:
        """
        یک پاسخ متنی برای پیام ورودی تولید می‌کند و به عنوان قرارداد باید توسط پیاده‌سازی‌های محدوده‌ی Chatbot ارائه شود.
        
        Parameters:
            message (str): متن ورودی که باید به آن پاسخ داده شود.
            context (Mapping[str, Any] | None): داده‌های زمینه‌ای اختیاری (مثلاً وضعیت جلسه، مشخصات کاربر، یا پارامترهای تنظیم) که پیاده‌سازی می‌تواند برای تولید پاسخ مرتبط از آن استفاده کند.
        
        Returns:
            reply (str): متن پاسخ تولیدشده برای پیام ورودی.
        """
        raise NotImplementedError