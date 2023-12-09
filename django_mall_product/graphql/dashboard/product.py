import uuid
import re

from django.core.exceptions import ValidationError
from django.db import connection, transaction

from graphene import ResolveInfo
from graphql_relay import from_global_id
from safedelete.models import HARD_DELETE
import graphene

from django_app_core.decorators import strip_input
from django_app_core.helpers.translation_helper import TranslationHelper
from django_app_core.relay.connection import DjangoFilterConnectionField
from django_app_core.types import TaskWarningType
from django_app_organization.models import Organization
from django_mall_product.graphql.dashboard.types.product import (
    ProductNode,
    ProductTransInput,
)
from django_mall_product.models import (
    Collection,
    CollectionProduct,
    Product,
    ProductTrans,
    ProductPlace,
    ProductSupplier,
    Variant,
)


class CreateProduct(graphene.relay.ClientIDMutation):
    class Input:
        slug = graphene.String(required=True)
        serial = graphene.String()
        sortKey = graphene.Int()
        priceAmount = graphene.Float()
        priceSaleAmount = graphene.Float(required=True)
        placeId = graphene.ID()
        supplierId = graphene.ID()
        collectionId = graphene.ID()
        collectionIds = graphene.List(graphene.ID)
        canSearch = graphene.Boolean()
        isPublished = graphene.Boolean()
        publishedAt = graphene.DateTime()
        translations = graphene.List(graphene.NonNull(ProductTransInput), required=True)

    success = graphene.Boolean()
    product = graphene.Field(ProductNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(
        cls,
        root,
        info: ResolveInfo,
        **input,
    ):
        slug = input["slug"]
        serial = input["serial"] if "serial" in input else None
        sortKey = input["sortKey"] if "sortKey" in input else None
        priceAmount = input["priceAmount"] if "priceAmount" in input else None
        priceSaleAmount = input["priceSaleAmount"]
        placeId = input["placeId"] if "placeId" in input else None
        supplierId = input["supplierId"] if "supplierId" in input else None
        collectionId = input["collectionId"] if "collectionId" in input else None
        collectionIds = input["collectionIds"] if "collectionIds" in input else []
        canSearch = input["canSearch"] if "canSearch" in input else True
        isPublished = input["isPublished"] if "isPublished" in input else False
        publishedAt = input["publishedAt"] if "publishedAt" in input else None
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="product", translations=translations
        )
        if not result:
            raise ValidationError(message)

        if (
            not slug
            or re.search(r"\W", slug.replace("-", ""))
            or any(str in slug for str in ["\\"])
        ):
            raise ValidationError("The slug is invalid!")
        if priceAmount and float(priceAmount) < 0:
            raise ValidationError("The priceAmount must be a positive number or zero!")
        elif priceSaleAmount and float(priceSaleAmount) < 0:
            raise ValidationError(
                "The priceSaleAmount must be a positive number or zero!"
            )

        if placeId:
            try:
                _, place_id = from_global_id(placeId)
                ProductPlace.objects.only("id").get(id=place_id)
            except:
                raise Exception("Can not find this productPlace!")
        else:
            place_id = None

        if supplierId:
            try:
                _, supplier_id = from_global_id(supplierId)
                ProductSupplier.objects.only("id").get(id=supplier_id)
            except:
                raise Exception("Can not find this productSupplier!")
        else:
            supplier_id = None

        organization = Organization.objects.only("id").get(
            schema_name=connection.schema_name
        )

        collection_id = None
        if collectionId:
            if collectionId not in collectionIds:
                raise ValidationError("The collectionId must in collectionIds!")
            try:
                _, collection_id = from_global_id(collectionId)
            except:
                raise Exception("Can not find this collection!")

        collections = []
        if collectionIds:
            for collectionId in collectionIds:
                try:
                    _, _id = from_global_id(collectionId)

                    collection = Collection.objects.only("id").get(pk=_id)
                    collections.append(collection)
                except:
                    raise Exception("Can not find some collection!")

        if (
            Product.objects.only("id")
            .filter(organization_id=organization.id, slug=slug)
            .exists()
        ):
            raise ValidationError("The slug is already in use!")
        else:
            product = Product.objects.create(
                organization_id=organization.id,
                place_id=place_id,
                supplier_id=supplier_id,
                slug=slug,
                serial=serial,
                sort_key=sortKey,
                can_search=canSearch,
                is_published=isPublished,
                published_at=publishedAt,
            )
            for translation in translations:
                product.translations.create(
                    language_code=translation["language_code"],
                    name=translation["name"],
                    description=translation["description"],
                    summary=translation["summary"],
                    content=translation["content"],
                )

            Variant.objects.create(
                product=product,
                slug=str(uuid.uuid4()).replace("-", ""),
                sku=None,
                price_amount=priceAmount,
                price_sale_amount=priceSaleAmount,
                is_primary=True,
                is_published=isPublished,
                published_at=publishedAt,
            )

            if collections:
                for collection in collections:
                    product.collections.add(collection)
                if collection_id:
                    CollectionProduct.objects.filter(
                        collection_id=collection_id, product=product
                    ).update(is_primary=True)

        return CreateProduct(success=True, product=product)


class DeleteProductBatch(graphene.relay.ClientIDMutation):
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
                _, product_id = from_global_id(id)
            except:
                warnings["error"].append(id)

            try:
                product = Product.objects.only("id").get(pk=product_id)
                product.delete()

                warnings["done"].append(id)
            except Product.DoesNotExist:
                warnings["not_found"].append(id)

        return DeleteProductBatch(success=True, warnings=warnings)


class UpdateProduct(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        slug = graphene.String(required=True)
        serial = graphene.String()
        sortKey = graphene.Int()
        priceAmount = graphene.Float()
        priceSaleAmount = graphene.Float(required=True)
        placeId = graphene.ID()
        supplierId = graphene.ID()
        collectionId = graphene.ID()
        collectionIds = graphene.List(graphene.ID)
        canSearch = graphene.Boolean()
        isPublished = graphene.Boolean()
        publishedAt = graphene.DateTime()
        translations = graphene.List(graphene.NonNull(ProductTransInput), required=True)

    success = graphene.Boolean()
    product = graphene.Field(ProductNode)

    @classmethod
    @strip_input
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        id = input["id"]
        slug = input["slug"]
        serial = input["serial"] if "serial" in input else None
        sortKey = input["sortKey"] if "sortKey" in input else None
        priceAmount = input["priceAmount"] if "priceAmount" in input else None
        priceSaleAmount = input["priceSaleAmount"]
        placeId = input["placeId"] if "placeId" in input else None
        supplierId = input["supplierId"] if "supplierId" in input else None
        collectionId = input["collectionId"] if "collectionId" in input else None
        collectionIds = input["collectionIds"] if "collectionIds" in input else []
        canSearch = input["canSearch"] if "canSearch" in input else True
        isPublished = input["isPublished"] if "isPublished" in input else False
        publishedAt = input["publishedAt"] if "publishedAt" in input else None
        translations = input["translations"]

        translation_helper = TranslationHelper()
        result, message = translation_helper.validate_translations_from_input(
            label="product", translations=translations
        )
        if not result:
            raise ValidationError(message)

        if (
            not slug
            or re.search(r"\W", slug.replace("-", ""))
            or any(str in slug for str in ["\\"])
        ):
            raise ValidationError("The slug is invalid!")
        if priceAmount and float(priceAmount) < 0:
            raise ValidationError("The priceAmount must be a positive number or zero!")
        elif priceSaleAmount and float(priceSaleAmount) < 0:
            raise ValidationError(
                "The priceSaleAmount must be a positive number or zero!"
            )

        if placeId:
            try:
                _, place_id = from_global_id(placeId)
                ProductPlace.objects.only("id").get(id=place_id)
            except:
                raise Exception("Can not find this productPlace!")
        else:
            place_id = None

        if supplierId:
            try:
                _, supplier_id = from_global_id(supplierId)
                ProductSupplier.objects.only("id").get(id=supplier_id)
            except:
                raise Exception("Can not find this productSupplier!")
        else:
            supplier_id = None

        try:
            _, product_id = from_global_id(id)
        except:
            raise Exception("Bad Request!")

        organization = Organization.objects.only("id").get(
            schema_name=connection.schema_name
        )

        collection_id = None
        if collectionId:
            if collectionId not in collectionIds:
                raise ValidationError("The collectionId must in collectionIds!")
            try:
                _, collection_id = from_global_id(collectionId)
            except:
                raise Exception("Can not find this collection!")

        collections = []
        if collectionIds:
            for collectionId in collectionIds:
                try:
                    _, _id = from_global_id(collectionId)

                    collection = Collection.objects.only("id").get(pk=_id)
                    collections.append(collection)
                except:
                    raise Exception("Can not find some collection!")

        if (
            Product.objects.exclude(pk=product_id)
            .filter(organization_id=organization.id, slug=slug)
            .exists()
        ):
            raise ValidationError("The slug is already in use!")
        else:
            try:
                product = Product.objects.get(
                    organization_id=organization.id, pk=product_id
                )
                product.place_id = place_id
                product.supplier_id = supplier_id
                product.slug = slug
                product.serial = serial
                product.sort_key = sortKey
                product.can_search = canSearch
                product.is_published = isPublished
                product.published_at = publishedAt
                product.save()

                for translation in translations:
                    ProductTrans.objects.update_or_create(
                        product=product,
                        language_code=translation["language_code"],
                        defaults={
                            "name": translation["name"],
                            "description": translation["description"],
                            "summary": translation["summary"],
                            "content": translation["content"],
                        },
                    )

                variant = Variant.objects.get(
                    product=product,
                    is_primary=True,
                )
                variant.sku = None
                variant.price_amount = priceAmount
                variant.price_sale_amount = priceSaleAmount
                variant.is_published = isPublished
                variant.save()

                collectionproduct_set_collections = product.collectionproduct_set.all()
                for collection in collectionproduct_set_collections:
                    collection.delete(force_policy=HARD_DELETE)
                if collections:
                    for collection in collections:
                        product.collections.add(collection)
                    if collection_id:
                        CollectionProduct.objects.filter(product=product).update(
                            is_primary=False
                        )
                        CollectionProduct.objects.filter(
                            collection_id=collection_id, product=product
                        ).update(is_primary=True)
            except Product.DoesNotExist:
                raise Exception("Can not find this product!")
            except Variant.DoesNotExist:
                raise Exception("Can not find this variant!")

        return UpdateProduct(success=True, product=product)


class ProductMutation(graphene.ObjectType):
    product_create = CreateProduct.Field()
    product_delete_batch = DeleteProductBatch.Field()
    product_update = UpdateProduct.Field()


class ProductQuery(graphene.ObjectType):
    product = graphene.relay.Node.Field(ProductNode)
    products = DjangoFilterConnectionField(
        ProductNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
