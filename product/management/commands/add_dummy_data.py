import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from product.factories import OfferFactory
from user.factories import UserFactory


class Command(BaseCommand):
    help = 'Generates dummy data, a combination of products and offers for those products'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', default=None)
        parser.add_argument('range', nargs='?', default=None, type=int)

    def create_user(self, **params):
        try:
            user = UserFactory(
                **params
            )
        except:
            user = get_user_model().objects.get(**params)

        user.set_password('a')

        # to allow this user to log into django admin and modify stuff
        user.is_superuser = True
        user.is_staff = True
        user.save()

        print(f"--- Created user with username: {user.username}")
        print(f"--- With the password: a")

        return user

    def handle(self, *args, **options):
        user = None
        if options['username']:
            try:
                user = get_user_model().objects.get(
                    username=options['username']
                )
            except get_user_model().DoesNotExist:
                user = self.create_user(username=options['username'])

        if not user:
            user = self.create_user()

        amount = options['range'] or random.randint(50,500)

        for i in range(amount):
            OfferFactory()

        print(f"--- Added {amount} products")
