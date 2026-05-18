"""Factory Boy factories for core test models."""

from django.db import models
import factory

from apps.core.models import BaseModel


class CoreDummy(BaseModel):
    name = models.CharField(max_length=10, blank=False, null=False)

    class Meta(BaseModel.Meta):
        app_label = "core"
        db_table = "core_dummy"


class CoreDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoreDummy

    name = factory.Sequence(lambda n: f"name{n}")
