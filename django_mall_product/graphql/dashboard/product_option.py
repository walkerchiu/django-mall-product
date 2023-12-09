from django.core.exceptions import ValidationError
from django.db import transaction

from graphene import ResolveInfo
from graphql_relay import from_global_id
import graphene

from django_app_core.decorators import strip_input
from django_app_core.helpers.translation_helper import TranslationHelper
from django_app_core.relay.connection import DjangoFilterConnectionField
from django_app_core.types import TaskWarningType
from django_mall_product.graphql.dashboard.types.product_option import (
    ProductOptionNode,
    ProductOptionTransInput,
)
from django_mall_product.models import Product, ProductOption, ProductOptionTrans


class CreateProductOption(graphene.relay.ClientIDMutation):
    class Input:
        productId = graphene.ID(required=True)
        sortKey = graphene.Int(required=True)
        translations = graphene.List(
            graphene.NonNull(ProductOptionTransInput), required=True
        )

    success = graphene.Boolean()
    product_option = graphene.Field(ProductOptionNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(
        cls,
        root,
        info: ResolveInfo,
        **input,
    ):
        productId = input["productId"]
        sortKey = input["sortKey"]
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="productOption", translations=translations
        )
        if not result:
            raise ValidationError(message)

        try:
            _, product_id = from_global_id(productId)
        except:
            raise Exception("Can not find this product!")

        product = Product.objects.filter(pk=product_id).first()
        if product is None:
            raise Exception("Can not find this product!")
        else:
            product_option = ProductOption.objects.create(
                product=product,
                sort_key=sortKey,
            )
            for translation in translations:
                product_option.translations.create(
                    language_code=translation["language_code"],
                    name=translation["name"],
                )

        return CreateProductOption(success=True, product_option=product_option)


class DeleteProductOptionBatch(graphene.relay.ClientIDMutation):
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
                _, product_option_id = from_global_id(id)
            except:
                warnings["error"].append(id)

            try:
                product_option = ProductOption.objects.only("id").get(
                    pk=product_option_id
                )
                product_option.delete()

                warnings["done"].append(id)
            except ProductOption.DoesNotExist:
                warnings["not_found"].append(id)

        return DeleteProductOptionBatch(success=True, warnings=warnings)


class UpdateProductOption(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        sortKey = graphene.Int(required=True)
        translations = graphene.List(
            graphene.NonNull(ProductOptionTransInput), required=True
        )

    success = graphene.Boolean()
    product_option = graphene.Field(ProductOptionNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        id = input["id"]
        sortKey = input["sortKey"]
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="productOption", translations=translations
        )
        if not result:
            raise ValidationError(message)

        try:
            _, product_id = from_global_id(id)

            Product.objects.only("id").get(pk=product_id)
        except:
            raise Exception("Bad Request!")

        try:
            product_option = ProductOption.objects.get(pk=product_id)
            product_option.sort_key = sortKey
            product_option.save()

            for translation in translations:
                ProductOptionTrans.objects.update_or_create(
                    product_option=product_option,
                    language_code=translation["language_code"],
                    defaults={
                        "name": translation["name"],
                    },
                )
        except ProductOption.DoesNotExist:
            raise Exception("Can not find this productOption!")

        return UpdateProductOption(success=True, product_option=product_option)


class ProductOptionMutation(graphene.ObjectType):
    product_option_create = CreateProductOption.Field()
    product_option_delete_batch = DeleteProductOptionBatch.Field()
    product_option_update = UpdateProductOption.Field()


class ProductOptionQuery(graphene.ObjectType):
    product_option = graphene.relay.Node.Field(ProductOptionNode)
    product_options = DjangoFilterConnectionField(
        ProductOptionNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
