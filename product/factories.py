import random, factory, json

from product.models import Offer, Product
from factory import Faker

from user.factories import UserFactory

fake = Faker


def get_random_size():
    return random.choice(["Small", "Medium", "Large", "Frozen", "Hand-Picked", "Premium", "Short-Dated"])


def get_random_color():
    return random.choice(["Red", "Orange", "Yellow", "Green", "Purple", "Pink", "White", "Burgundy"])


def coin_toss():
    return random.choice([0, 1])


def get_random_item():
    json_data = open('generic_product_data.json')
    data = json.load(json_data)
    product_type = random.choice(list(data.keys()))
    item_name = " ".join([random.choice(data[product_type]), product_type[:-1]]).title()

    if coin_toss():
        item_name = " ".join([get_random_color(), item_name])

    if coin_toss():
        item_name = " ".join([get_random_size(), item_name])

    return item_name


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    height = fake("random_int", min=300, max=999)
    width = fake("random_int", min=300, max=999)
    length = fake("random_int", min=300, max=999)
    weight = fake("random_int", min=1, max=9)

    @factory.lazy_attribute
    def name(self):
        def generate_name():
            name = get_random_item()
            try:
                Product.objects.get(name=name)
            except Product.DoesNotExist:
                return name
            return generate_name()
        return generate_name()

    @factory.LazyAttribute
    def gtin(self):
        def generate_gtin():
            gtin = fake._get_faker().ean13()
            try:
                Product.objects.get(gtin=gtin)
            except Product.DoesNotExist:
                return gtin
            return generate_gtin()
        return generate_gtin()


class OfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Offer

    quantity = fake("random_int", min=0, max=20)
    seller_price = fake("random_int", min=1, max=99)
    product = factory.SubFactory(ProductFactory)
    seller = factory.SubFactory(UserFactory)
