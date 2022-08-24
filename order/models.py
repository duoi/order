from django.db import models, transaction
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError

from product.models import Product
from supply.generics.mixins import ModelWithDatetime


class OrderLine(ModelWithDatetime):
    """
    Each individual order line for an order lives here. From this we can
    generate proformas, qualify a sale, and generate invoices.
    """
    seller = models.ForeignKey(
        to="user.User",
        on_delete=models.CASCADE,
        help_text="The seller that is supplying this item"
    )
    quantity = models.PositiveIntegerField(
        help_text="Quantity that has been ordered"
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="The accepted net price for this order line"
    )
    product = models.ForeignKey(
        to="product.Product",
        help_text="The product that is being purchased",
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        to="order.Order",
        on_delete=models.CASCADE,
        help_text="The order that this order line relates to",
        related_name="lines"
    )

    @cached_property
    def subtotal(self):
        return round(float(self.price) * self.quantity, 2)


class OrderManager(models.Manager):
    def get_or_create_open_order_for_user(self, user):
        return self.get_or_create(buyer=user, is_confirmed=False)


class Order(ModelWithDatetime):
    """
    The core order/cart model.
    """
    buyer = models.ForeignKey(
        to="user.User",
        on_delete=models.CASCADE,
        help_text="The buyer that placed the order"
    )
    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="The shipping costs associated with this order",
        default=0
    )
    vat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="The VAT value of this order",
        default=0
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="The subtotal represents the individual item value (excluding shipping costs, excluding VAT)",
        default=0,
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="The total value of this order",
        default=0,
    )
    # doing the below in lieu of a separate way to store a cart, this can probably
    # be refined a bit better but time constraints lead me to this approach
    is_confirmed = models.BooleanField(
        default=False,
        help_text="Whether or not this order has been placed or is still pending"
    )

    objects = OrderManager()

    def calculate_totals(self):
        vat_amount = 0.21  # assume constant VAT for this exercise, usually would come from buyer location
        shipping_cost = 15.00  # assume flat shipping cost for this exercise

        items = self.lines.values("price", "quantity")
        self.subtotal = float(sum((item["price"] * item["quantity"]) for item in items))
        self.shipping_cost = shipping_cost
        self.vat = (self.subtotal + self.shipping_cost) * vat_amount
        self.total = self.subtotal + self.shipping_cost + self.vat
        self.save(update_fields=["subtotal", "shipping_cost", "vat", "total"])

    def checkout(self):
        """
        1. Get list of items in cart
        2. Get matching products
        3. Compare quantities -- make sure it hasn't sold out since adding to cart
        4. If it has sold out, appropriately remove the items or update the quantities

        This can be better refined, probably moved elsewhere with clearer messaging on
        what has changed. Maybe even put the out-of-stock items into a wishlist or
        something to notify them about when its back in stock.
        """
        order_lines = self.lines.all().select_related("product")
        products = Product.objects.select_for_update().filter(
            id__in=order_lines.values_list("product_id")
        )
        with transaction.atomic():
            existing_orderlines_to_update = []
            existing_orderlines_to_delete = []
            for item in products:
                matching_order_line = order_lines.get(product_id=item.id)
                if item.quantity >= matching_order_line.quantity:
                    item.reduce_quantity(matching_order_line.quantity)
                elif item.quantity > 0:
                    matching_order_line.quantity = item.quantity
                    existing_orderlines_to_update.append(matching_order_line)
                elif item.quantity == 0:
                    existing_orderlines_to_delete.append(matching_order_line.id)

            if existing_orderlines_to_update:
                OrderLine.objects.bulk_update(existing_orderlines_to_update, ["quantity"])
            if existing_orderlines_to_delete:
                OrderLine.objects.filter(id__in=existing_orderlines_to_delete).delete()

        if existing_orderlines_to_update or existing_orderlines_to_delete:
            self.calculate_totals()
            raise ValidationError(
                "Some of your chosen items have since become out of stock or no longer have sufficient "
                "quantity. Please review your updated cart."
            )
        # if the product price was a database field i could do something like the below:
        # order_lines.update(price=F("product__price"))
        #
        # but because for this exercise it's not, and i don't have time to refactor, i
        # have to do the more expensive/uglier code below
        for item in order_lines:
            item.price = item.product.price
            item.save()

        self.is_confirmed = True
        self.save(update_fields=["is_confirmed"])
