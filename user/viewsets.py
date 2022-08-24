from rest_framework import mixins, response, viewsets
from rest_framework.permissions import AllowAny

from user.serializers import AuthenticationSerializer


class AuthenticationViewset(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = AuthenticationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.get_token(serializer.validated_data)

        return response.Response({"token": f"Token {token}"})