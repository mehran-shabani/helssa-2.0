from django.contrib import admin

from .models import BoxMoney, Subscription

admin.site.register(Subscription)
admin.site.register(BoxMoney)
