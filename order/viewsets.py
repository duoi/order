from rest_framework import response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from order.models import Order
from order.serializers import AddToCartSerializer, OrderSerializer
from supply.generics.viewsets import QualifiedViewSet


class OrderViewSet(QualifiedViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()

    def get_queryset(self):
        return self.queryset.filter(buyer=self.request.user).exclude(is_confirmed=False)

    # note: the following two don't act on the detail route, just the list route.
    # this is based on the assumption that a user can only have one open cart at
    # any one time. if we want to support multiple carts, then this should act on
    # the detail route instead.
    @action(methods=['POST'], detail=False, serializer_class=AddToCartSerializer)
    def update_cart(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        open_cart, _ = Order.objects.get_or_create_open_order_for_user(self.request.user)
        obj = serializer.add(open_cart, validated_data)

        return response.Response(status=200, data=OrderSerializer(instance=obj).data)

    @action(methods=['POST'], detail=False, serializer_class=OrderSerializer)
    def checkout(self, request):
        """
        This is set as a POST request to avoid accidental trigger, i.e through browser prefetching

        In reality the checkout flow would probably be a bit more complicated, selecting billing
        and shipping addresses and payment methods or financing requests etc.
        """
        cart = self.queryset.filter(buyer=self.request.user, is_confirmed=False).first()
        if not cart or not cart.subtotal > 0:
            raise ValidationError("Please make sure you have items in your cart.")
        cart.checkout()
        return self.list(request)

    @action(methods=['GET'], detail=False, serializer_class=OrderSerializer)
    def cart(self, request):
        """
        Returns the active cart, or creates one and returns it
        """
        cart, _ = Order.objects.get_or_create_open_order_for_user(request.user)
        serializer = OrderSerializer(instance=cart)
        return response.Response(status=200, data=serializer.data)
