from rest_framework.mixins import (
    RetrieveModelMixin,
    ListModelMixin,
)
from rest_framework.viewsets import GenericViewSet


class QualifiedViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet
):
    pass
