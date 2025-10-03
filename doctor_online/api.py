from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from .models import Visit


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ["id", "user", "created_at", "note"]
        read_only_fields = fields


class VisitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VisitSerializer
    permission_classes = [IsAdminUser]
    queryset = Visit.objects.select_related("user").order_by("-created_at")
