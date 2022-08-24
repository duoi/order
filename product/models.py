from django.db import models
from django.utils.functional import cached_property

from supply.generics.mixins import ModelWithDatetime
from django.db.models import Avg, F, Sum


class Product(ModelWithDatetime):
    """
    A constant set of products, regardless of whether we have stock
    """
    name = models.TextField(
        help_text="Name of this product"
    )
    gtin = models.CharField(
        max_length=13,
        help_text="GTIN of this product, if any",
        default=None,
        null=True,
        blank=True,
        unique=True
    )
    weight = models.PositiveIntegerField(
        help_text="In kg"
    )
    length = models.PositiveIntegerField(
        help_text="In mm"
    )
    height = models.PositiveIntegerField(
        help_text="In mm"
    )
    width = models.PositiveIntegerField(
        help_text="In mm"
    )
    image = models.URLField(
        default=None,
        null=True,
        blank=True,
        help_text="The image of this product, if any"
    )

    @cached_property
    def in_stock(self):
        return self.offers.exists()

    @cached_property
    def price(self):
        """
        This would probably be a database field in practice, but it would be the
        price that we choose to sell it at: i.e, taking out some offers that are
        some std deviation from the median then taking an average across the
        remaining with some margin added.
        """
        seller_price = self.offers.annotate(
            average_price=Avg('seller_price')
        ).values("average_price")[0]["average_price"]

        return round(float(seller_price) * 1.12, 2)  # some margin

    @cached_property
    def quantity(self):
        """
        This should probably be a database field that is updated at the time
        that stock lists from sellers are refreshed, it's not worth the
        additional db hit
        """
        return self.offers.aggregate(Sum('quantity')).get("quantity__sum")

    def reduce_quantity(self, reserved):
        """
        This is fairly basic for this exercise, as there is a single offer available.
        In practice, reducing quantity availability would depend on several factors
        and it's significantly out of scope for this exercise.
        """
        return self.offers.update(quantity=F("quantity")-reserved)


class Offer(ModelWithDatetime):
    """
    Individual offers from sellers for each product
    """
    quantity = models.PositiveIntegerField(
        help_text="Available quantity for this offer"
    )
    seller_price = models.DecimalField(
        help_text="The price for this offer from the seller",
        decimal_places=2,
        max_digits=12
    )
    # there should probably be a field here to capture the currency, i.e PLN vs EUR vs GBP
    seller = models.ForeignKey(
        to="user.User",
        help_text="The seller from whom this offer is being made",
        related_name="offers",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        to="product.Product",
        help_text="The product this offer is for",
        related_name="offers",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('seller', 'product',)  # prevent duplicate/staggered offers from same sellers
