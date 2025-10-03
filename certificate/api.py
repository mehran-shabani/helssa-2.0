from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ["id", "owner", "title", "body", "created_at"]
        read_only_fields = fields


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        بازگشت یک queryset از نمونه‌های Certificate متناسب با کاربر جاری.
        
        برای بهینه‌سازی، کوئری پایه شامل select_related("owner") و مرتب‌سازی نزولی بر اساس created_at است. اگر کاربر جاری staff باشد، همهٔ رکوردها بازگردانده می‌شوند؛ در غیر اینصورت فقط Certificateهایی که owner آن‌ها برابر با کاربر جاری است بازمی‌گردد.
        
        Returns:
            QuerySet: مجموعه‌ای از اشیاء Certificate مطابق با دسترسی کاربر و مرتب‌شده بر اساس created_at به صورت نزولی.
        """
        queryset = Certificate.objects.select_related("owner").order_by("-created_at")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(owner=user)