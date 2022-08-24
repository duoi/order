from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        read_only=True
    )
    name = serializers.CharField(
        read_only=True,
    )
    gtin = serializers.CharField(
        help_text="GTIN of this product, if any",
        read_only=True,
    )
    weight = serializers.CharField(
        help_text="In kg",
        read_only=True,
    )
    length = serializers.CharField(
        help_text="In mm",
        read_only=True,
    )
    height = serializers.CharField(
        help_text="In mm",
        read_only=True,
    )
    width = serializers.CharField(
        help_text="In mm",
        read_only=True,
    )
    image = serializers.URLField(
        help_text="The image of this product, if any",
        read_only=True,
    )
    price = serializers.CharField(
        help_text="The price of the product",
        read_only=True,
    )
    quantity = serializers.IntegerField(
        help_text="Available, sellable inventory amount",
        read_only=True,
    )
