from rest_framework import serializers
from .models import ImportLog

class ImportLogSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an ImportLog.
    
    Provides monitoring data for the import pipeline. Write operations
    are explicitly disabled to ensure data integrity.
    """
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ImportLog
        fields = [
            "id",
            "source",
            "status",
            "records_total",
            "records_imported",
            "records_failed",
            "started_at",
            "finished_at",
            "duration",
            "error_message",
        ]
        # Ensure all fields are read-only at the serializer level
        read_only_fields = fields

    def get_duration(self, obj):
        """Calculate the total processing time."""
        if obj.finished_at and obj.started_at:
            delta = obj.finished_at - obj.started_at
            return str(delta).split(".")[0]  # Returns HH:MM:SS
        return None

    def create(self, validated_data):
        """Prevent creation of logs via the API."""
        raise serializers.ValidationError("Import logs cannot be created via the API.")

    def update(self, instance, validated_data):
        """Prevent modification of logs via the API."""
        raise serializers.ValidationError("Import logs cannot be updated via the API.")