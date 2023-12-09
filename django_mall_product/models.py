import uuid

from django.conf import settings
from django.db import models

from django_prices.models import MoneyField
from safedelete.models import SOFT_DELETE_CASCADE

from django_app_core.models import (
    CommonDateAndSafeDeleteMixin,
    PublishableModel,
    TranslationModel,
)


class Product(CommonDateAndSafeDeleteMixin, PublishableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(max_length=255, db_index=True)
    serial = models.CharField(max_length=255, db_index=True, null=True)
    sort_key = models.IntegerField(db_index=True, null=True)
    can_search = models.BooleanField(default=True)
    count_access = models.PositiveIntegerField(default=0)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product"
        get_latest_by = "updated_at"
        ordering = ["sort_key", "serial"]

    def __str__(self):
        return str(self.id)


class ProductTrans(CommonDateAndSafeDeleteMixin, TranslationModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product, related_name="translations", on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product_trans"
        index_together = (("language_code", "product"),)
        ordering = ["language_code"]

    def __str__(self):
        return str(self.id)


class ProductOption(CommonDateAndSafeDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, models.CASCADE)
    sort_key = models.IntegerField(db_index=True)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product_option"
        get_latest_by = "updated_at"
        ordering = ["sort_key"]

    def __str__(self):
        return str(self.id)


class ProductOptionTrans(CommonDateAndSafeDeleteMixin, TranslationModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_option = models.ForeignKey(
        ProductOption, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, db_index=True)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product_option_trans"
        get_latest_by = "updated_at"
        index_together = (("language_code", "product_option"),)
        ordering = ["language_code"]

    def __str__(self):
        return str(self.id)


class ProductOptionValue(CommonDateAndSafeDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_option = models.ForeignKey(ProductOption, models.CASCADE)
    sort_key = models.IntegerField(db_index=True)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product_option_value"
        get_latest_by = "updated_at"
        ordering = ["sort_key"]

    def __str__(self):
        return str(self.id)


class ProductOptionValueTrans(CommonDateAndSafeDeleteMixin, TranslationModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_option_value = models.ForeignKey(
        ProductOptionValue, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, db_index=True)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_product_option_value_trans"
        get_latest_by = "updated_at"
        index_together = (("language_code", "product_option_value"),)
        ordering = ["language_code"]

    def __str__(self):
        return str(self.id)


class Variant(CommonDateAndSafeDeleteMixin, PublishableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, models.CASCADE)
    selected_option_values = models.ManyToManyField(
        ProductOptionValue, through="VariantOptionValue"
    )
    slug = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    sku = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        default=settings.DEFAULT_CURRENCY_CODE,
    )
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    price_sale_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    price_sale = MoneyField(amount_field="price_sale_amount", currency_field="currency")
    is_primary = models.BooleanField(default=False)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_variant"
        get_latest_by = "updated_at"
        index_together = (
            ("product", "slug"),
            ("product", "sku"),
        )
        ordering = ["sku"]

    def __str__(self):
        return str(self.id)


class VariantOptionValue(CommonDateAndSafeDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(Variant, models.CASCADE)
    product_option_value = models.ForeignKey(ProductOptionValue, models.CASCADE)

    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        db_table = settings.APP_NAME + "_product_variant_optionvalues"
        get_latest_by = "updated_at"

    def __str__(self):
        return str(self.id)
