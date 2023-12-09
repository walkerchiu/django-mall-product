from django.core.exceptions import ValidationError
from django.db import transaction

from graphene import ResolveInfo
from graphql_relay import from_global_id
import graphene

from django_app_core.decorators import strip_input
from django_app_core.helpers.translation_helper import TranslationHelper
from django_app_core.relay.connection import DjangoFilterConnectionField
from django_app_core.types import TaskWarningType
from django_mall_product.graphql.dashboard.types.product_option_value import (
    ProductOptionValueNode,
    ProductOptionValueTransInput,
)
from django_mall_product.models import (
    ProductOption,
    ProductOptionValue,
    ProductOptionValueTrans,
)


class CreateProductOptionValue(graphene.relay.ClientIDMutation):
    class Input:
        productOptionId = graphene.ID(required=True)
        sortKey = graphene.Int(required=True)
        translations = graphene.List(
            graphene.NonNull(ProductOptionValueTransInput), required=True
        )

    success = graphene.Boolean()
    product_option_value = graphene.Field(ProductOptionValueNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(
        cls,
        root,
        info: ResolveInfo,
        **input,
    ):
        productOptionId = input["productOptionId"]
        sortKey = input["sortKey"]
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="productOptionValue", translations=translations
        )
        if not result:
            raise ValidationError(message)

        try:
            _, product_option_id = from_global_id(productOptionId)
        except:
            raise Exception("Can not find this productOption!")

        product_option = ProductOption.objects.filter(pk=product_option_id).first()
        if product_option is None:
            raise Exception("Can not find this productOption!")
        else:
            product_option_value = ProductOptionValue.objects.create(
                product_option=product_option,
                sort_key=sortKey,
            )
            for translation in translations:
                product_option_value.translations.create(
                    language_code=translation["language_code"],
                    name=translation["name"],
                )

        return CreateProductOptionValue(
            success=True, product_option_value=product_option_value
        )


class DeleteProductOptionValueBatch(graphene.relay.ClientIDMutation):
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
                product_option_value = ProductOptionValue.objects.only("id").get(
                    pk=product_option_id
                )
                product_option_value.delete()

                warnings["done"].append(id)
            except ProductOptionValue.DoesNotExist:
                warnings["not_found"].append(id)

        return DeleteProductOptionValueBatch(success=True, warnings=warnings)


class UpdateProductOptionValue(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        sortKey = graphene.Int(required=True)
        translations = graphene.List(
            graphene.NonNull(ProductOptionValueTransInput), required=True
        )

    success = graphene.Boolean()
    product_option_value = graphene.Field(ProductOptionValueNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        id = input["id"]
        sortKey = input["sortKey"]
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="productOptionValue", translations=translations
        )
        if not result:
            raise ValidationError(message)

        try:
            _, product_option_id = from_global_id(id)

            ProductOption.objects.only("id").get(pk=product_option_id)
        except:
            raise Exception("Bad Request!")

        try:
            product_option_value = ProductOptionValue.objects.get(pk=product_option_id)
            product_option_value.sort_key = sortKey
            product_option_value.save()

            for translation in translations:
                ProductOptionValueTrans.objects.update_or_create(
                    product_option_value=product_option_value,
                    language_code=translation["language_code"],
                    defaults={
                        "name": translation["name"],
                    },
                )
        except ProductOptionValue.DoesNotExist:
            raise Exception("Can not find this productOptionValue!")

        return UpdateProductOptionValue(
            success=True, product_option_value=product_option_value
        )


class ProductOptionValueMutation(graphene.ObjectType):
    product_option_value_create = CreateProductOptionValue.Field()
    product_option_value_delete_batch = DeleteProductOptionValueBatch.Field()
    product_option_value_update = UpdateProductOptionValue.Field()


class ProductOptionValueQuery(graphene.ObjectType):
    product_option_value = graphene.relay.Node.Field(ProductOptionValueNode)
    product_option_values = DjangoFilterConnectionField(
        ProductOptionValueNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
