from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from .models import APKDownloadStat


class APKDownloadStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = APKDownloadStat
        fields = ["id", "key", "count", "updated_at"]
        read_only_fields = fields


class APKStatsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = APKDownloadStatSerializer
    permission_classes = [IsAdminUser]
    queryset = APKDownloadStat.objects.all().order_by("-updated_at")
