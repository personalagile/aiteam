"""Serializers for the public API."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class EchoSerializer(serializers.Serializer):
    """Minimal example serializer used for quick tests."""

    message = serializers.CharField(max_length=2000)

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        return validated_data

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:  # pragma: no cover
        return instance
