from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from order.models import OrderLine
from product.models import Product


class OrderLinesSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        help_text="Requested inventory amount for this order line",
    )
    price = serializers.SerializerMethodField(
        help_text="The price of the product",
    )
    product = serializers.CharField(
        source="product.name",
        help_text="The name of the related product"
    )
    productId = serializers.IntegerField(
        source="product_id",
        help_text="The ID of the related product"
    )
    subtotal = serializers.CharField(
        help_text="The subtotal for this line item"
    )

    def get_price(self, obj):
        """
        This is a crude way of getting
        1. The current price if the order hasn't been checked out
        2. The original purchase price if the order has been checked out

        There can probably be some better work on this front, we probably
        want to store both on the order line table for future heuristics anyway
        """
        if obj.order.is_confirmed:
            return obj.price
        return obj.product.price


class OrderSerializer(serializers.Serializer):
    shipping_cost = serializers.CharField(
        read_only=True,
        help_text="The shipping costs associated with this order",
    )
    vat = serializers.CharField(
        read_only=True,
        help_text="The VAT value of this order",
    )
    subtotal = serializers.CharField(
        read_only=True,
        help_text="The subtotal represents the individual item value (excluding shipping costs, excluding VAT)",
    )
    total = serializers.CharField(
        read_only=True,
        help_text="The total value of this order",
    )
    is_confirmed = serializers.BooleanField(
        read_only=True,
        help_text="Whether or not this order has been finalized, i.e checked out"
    )
    lines = OrderLinesSerializer(
        many=True,
        help_text="The individual order lines associated to this order",
        required=False,
    )


class AddToCartSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        help_text="The primary key of the product"  # In practice this might be a UUID or a hashed version of the PK
    )
    quantity = serializers.IntegerField(
        help_text="How many units the user would like to order",
        min_value=0,
    )

    def add(self, cart, item):
        """
        This can probably come out of the serializer and live elsewhere, I had
        different plans initially so put it here but as it matured it stopped
        making as much sense.
        """
        existing_item = cart.lines.filter(product_id=item["id"])
        lines_to_add = []
        try:
            product = Product.objects.get(id=item["id"])
        except Product.DoesNotExist:
            raise ValidationError({"id": f"Product with ID {item['id']} does not exist."})

        if existing_item:
            if item["quantity"] == 0:
                existing_item.delete()
            elif item["quantity"] <= product.quantity:
                existing_item.update(quantity=item["quantity"])
            elif item["quantity"] > product.quantity:
                raise ValidationError({
                    "quantity": f"Requested quantity of product {product.name} exceeds stock levels, maximum "
                                f"quantity is {product.quantity}."
                })
            cart.calculate_totals()
            return cart

        if item["quantity"] == 0:
            raise ValidationError({"quantity": "Invalid quantity. Quantity must be at least 1"})
        elif item["quantity"] > product.quantity:
            raise ValidationError(
                {
                    "quantity": f"Requested quantity of product {product.name} exceeds stock levels, maximum "
                                f"quantity is {product.quantity}"
                }
            )
        """
        choose the offer at random. in practice this should be a whole microservice or something that
        1. takes into account historical seller performance to fulfill the order
        2. considers geographical proximity
        3. takes pricing into consideration
        4. takes MOQ amounts into consideration
        5. considers historical quality of the supplied product
        6. various other heuristics passed off to some ML megamind
        7. can split this across multiple sellers who offer different amounts
        """
        seller = product.offers.order_by("?").first().seller.id
        # add some handling to ensure that the item with that id actually exists
        lines_to_add.append(
            OrderLine(
                seller_id=seller,
                order=cart,
                product=product,
                price=product.price,
                quantity=item["quantity"]
            )
        )

        OrderLine.objects.bulk_create(lines_to_add)
        cart.calculate_totals()
        return cart