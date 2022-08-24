from django.contrib import admin

from order.models import Order, OrderLine

admin.site.register(OrderLine)
admin.site.register(Order)
