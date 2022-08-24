from django.contrib.auth import authenticate
from knox.models import AuthToken
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class AuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        write_only=True
    )
    password = serializers.CharField(
        required=True,
        write_only=True
    )

    def validate(self, attrs):
        super().validate(attrs)

        user = authenticate(**attrs)

        if not user:
            raise ValidationError("Invalid login credentials.")

        return user

    def get_token(self, user):
        _, token = AuthToken.objects.create(user=user)
        return token
