import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from graphene import ResolveInfo
from graphql_relay import from_global_id
import graphene

from django_app_core.decorators import strip_input
from django_app_core.relay.connection import DjangoFilterConnectionField
from django_app_core.types import TaskWarningType
from django_mall_product.graphql.dashboard.types.variant import VariantNode
from django_mall_product.models import (
    Product,
    ProductOption,
    ProductOptionValue,
    Variant,
    VariantOptionValue,
)


class CreateVariant(graphene.relay.ClientIDMutation):
    class Input:
        productId = graphene.ID(required=True)
        sku = graphene.String()
        priceAmount = graphene.Float()
        priceSaleAmount = graphene.Float(required=True)
        optionValues = graphene.List(graphene.ID, required=True)
        isPublished = graphene.Boolean()
        publishedAt = graphene.DateTime()

    success = graphene.Boolean()
    variant = graphene.Field(VariantNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        productId = input["productId"]
        sku = input["sku"] if "sku" in input else None
        priceAmount = input["priceAmount"] if "priceAmount" in input else None
        priceSaleAmount = input["priceSaleAmount"]
        optionValues = input["optionValues"]
        isPublished = input["isPublished"] if "isPublished" in input else False
        publishedAt = input["publishedAt"] if "publishedAt" in input else None

        if not productId:
            raise ValidationError("The productId is invalid!")
        if priceAmount and float(priceAmount) < 0:
            raise ValidationError("The priceAmount must be a positive number or zero!")
        elif priceSaleAmount and float(priceSaleAmount) < 0:
            raise ValidationError(
                "The priceSaleAmount must be a positive number or zero!"
            )

        try:
            _, product_id = from_global_id(productId)

            Product.objects.only("id").get(pk=product_id)
        except:
            raise Exception("Bad Request!")

        options = ProductOption.objects.only("id").filter(product_id=product_id)
        if len(optionValues) != len(options):
            raise ValidationError("The length of the optionValues is invalid!")

        valueList = []
        for optionValueId in optionValues:
            _, option_value_id = from_global_id(optionValueId)

            product_option_value = ProductOptionValue.objects.filter(
                pk=option_value_id
            ).first()
            if (
                not product_option_value
                or product_option_value.product_option_id in valueList
            ):
                raise ValidationError("The optionValues is invalid!")
            valueList.append(option_value_id)

        if (
            Variant.objects.filter(product_id=product_id, sku=sku)
            .exclude(sku__isnull=True)
            .exists()
        ):
            raise ValidationError("The sku is already in use!")
        else:
            variant = Variant()
            variant.product_id = product_id
            variant.slug = str(uuid.uuid4()).replace("-", "")
            variant.sku = sku
            variant.price_amount = priceAmount
            variant.price_sale_amount = priceSaleAmount
            variant.is_published = isPublished
            variant.published_at = publishedAt
            variant.is_primary = False
            variant.save()

            for product_option_value_id in valueList:
                VariantOptionValue.objects.create(
                    variant=variant, product_option_value_id=product_option_value_id
                )

        return CreateVariant(success=True, variant=variant)


class DeleteVariantBatch(graphene.relay.ClientIDMutation):
    class Input:
        idList = graphene.List(graphene.ID, required=True)

    success = graphene.Boolean()
    warnings = graphene.Field(TaskWarningType)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        idList = input["idList"] if "idList" in input else []

        warnings = {
            "done": [],
            "error": [],
            "in_protected": [],
            "in_use": [],
            "not_found": [],
        }

        for id in idList:
            try:
                _, variant_id = from_global_id(id)
            except:
                warnings["error"].append(id)

            try:
                variant = Variant.objects.only("is_primary").get(pk=variant_id)
                if variant.is_primary:
                    warnings["in_protected"].append(id)
                variant.delete()

                warnings["done"].append(id)
            except Variant.DoesNotExist:
                warnings["not_found"].append(id)

        return DeleteVariantBatch(success=True, warnings=warnings)


class UpdateVariant(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        productId = graphene.ID(required=True)
        sku = graphene.String()
        priceAmount = graphene.Float()
        priceSaleAmount = graphene.Float(required=True)
        optionValues = graphene.List(graphene.ID, required=True)
        isPublished = graphene.Boolean()
        publishedAt = graphene.DateTime()

    success = graphene.Boolean()
    variant = graphene.Field(VariantNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        id = input["id"]
        productId = input["productId"]
        sku = input["sku"] if "sku" in input else None
        priceAmount = input["priceAmount"] if "priceAmount" in input else None
        priceSaleAmount = input["priceSaleAmount"]
        optionValues = input["optionValues"]
        isPublished = input["isPublished"] if "isPublished" in input else False
        publishedAt = input["publishedAt"] if "publishedAt" in input else None

        if priceAmount and float(priceAmount) < 0:
            raise ValidationError("The priceAmount must be a positive number or zero!")
        elif priceSaleAmount and float(priceSaleAmount) < 0:
            raise ValidationError(
                "The priceSaleAmount must be a positive number or zero!"
            )

        try:
            _, variant_id = from_global_id(id)
            _, product_id = from_global_id(productId)

            Product.objects.only("id").get(pk=product_id)
        except:
            raise Exception("Bad Request!")

        options = ProductOption.objects.filter(product_id=product_id)
        if len(optionValues) != len(options):
            raise ValidationError("The length of the optionValues is invalid!")

        valueList = []
        for optionValueId in optionValues:
            _, option_value_id = from_global_id(optionValueId)

            product_option_value = ProductOptionValue.objects.filter(
                pk=option_value_id
            ).first()
            if (
                not product_option_value
                or product_option_value.product_option_id in valueList
            ):
                raise ValidationError("The optionValues is invalid!")
            valueList.append(option_value_id)

        if (
            Variant.objects.exclude(pk=variant_id)
            .filter(product_id=product_id, sku=sku)
            .exclude(sku__isnull=True)
            .exists()
        ):
            raise ValidationError("The sku is already in use!")
        else:
            try:
                variant = Variant.objects.get(pk=variant_id, product_id=product_id)
                if variant.is_primary:
                    raise Exception("This operation is not allowed!")
                variant.sku = sku
                variant.price_amount = priceAmount
                variant.price_sale_amount = priceSaleAmount
                variant.is_published = isPublished
                variant.published_at = publishedAt
                variant.is_primary = False
                variant.save()

                VariantOptionValue.objects.filter(variant=variant).exclude(
                    product_option_value_id__in=valueList
                ).delete()
                for product_option_value_id in valueList:
                    VariantOptionValue.objects.get_or_create(
                        variant=variant, product_option_value_id=product_option_value_id
                    )
            except Variant.DoesNotExist:
                raise Exception("Can not find this variant!")

        return UpdateVariant(success=True, variant=variant)


class VariantMutation(graphene.ObjectType):
    variant_create = CreateVariant.Field()
    variant_delete_batch = DeleteVariantBatch.Field()
    variant_update = UpdateVariant.Field()


class VariantQuery(graphene.ObjectType):
    variant = graphene.relay.Node.Field(VariantNode)
    variants = DjangoFilterConnectionField(
        VariantNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
