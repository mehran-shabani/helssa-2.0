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
        queryset = Certificate.objects.select_related("owner").order_by("-created_at")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(owner=user)
