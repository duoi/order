from rest_framework.permissions import IsAuthenticated

from product.models import Product
from product.serializers import ProductSerializer
from supply.generics.viewsets import QualifiedViewSet


class ProductViewSet(QualifiedViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    # limit the products to only ones with active offers. in
    # practice, maybe remove products with 0 quantity as well
    queryset = Product.objects.filter(
        offers__isnull=False
    )
