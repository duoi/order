from django.db import models


class ModelWithDatetime(models.Model):
    date_created = models.DateTimeField(
        help_text="The datetime this was created",
        auto_now_add=True
    )
    date_updated = models.DateTimeField(
        help_text="The datetime this was updated",
        auto_now=True
    )

    class Meta:
        abstract = True
