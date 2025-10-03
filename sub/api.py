from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BoxMoney, Subscription


class MeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tokens = (
            Subscription.objects.filter(user=user).values_list("tokens", flat=True).first()
            or 0
        )
        balance = (
            BoxMoney.objects.filter(user=user).values_list("balance", flat=True).first() or 0
        )
        return Response({"tokens": tokens, "balance": balance})
