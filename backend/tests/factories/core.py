import factory
from django.db import models
from django.apps import apps

from apps.core.model import BaseModel

class CoreDummy(BaseModel):
    name = models.CharField(max_length=10, blank=False, null=False)

    class Meta(BaseModel.Meta):
        app_label = "core"
        db_table = "core_dummy"


class CoreDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoreDummy

    name = factory.Sequence(lambda n: f"name{n}")