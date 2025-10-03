from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BoxMoney, Subscription


class MeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        مشخصات اشتراک و موجودی حساب کاربر احرازشده را برمی‌گرداند.
        
        این متد از کاربر جاری در درخواست استفاده می‌کند، تعداد توکن‌های مرتبط با اشتراک کاربر را بازیابی می‌کند و در صورت نبود مقدار، مقدار پیش‌فرض 0 را قرار می‌دهد. همچنین موجودی (balance) حساب کاربر را بازیابی کرده و در صورت نبود مقدار، 0 در نظر می‌گیرد. نهایتاً یک پاسخ JSON شامل دو کلید `tokens` و `balance` بازمی‌گرداند.
        
        Parameters:
            request (rest_framework.request.Request): درخواست HTTP حاوی کاربر احرازشده در `request.user`.
        
        Returns:
            dict: دیکشنری با کلیدهای `tokens` (تعداد توکن‌های اشتراک، عدد صحیح) و `balance` (موجودی حساب، عددی).
        """
        user = request.user
        try:
            tokens = user.subscription.tokens
        except Subscription.DoesNotExist:
            tokens = 0
        try:
            balance = user.boxmoney.balance
        except BoxMoney.DoesNotExist:
            balance = 0
        return Response({"tokens": tokens, "balance": balance})