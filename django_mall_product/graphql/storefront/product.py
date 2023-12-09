from django.db import connection, transaction

from graphene import ResolveInfo
from graphql_relay import from_global_id
import graphene

from django_app_core.relay.connection import DjangoFilterConnectionField
from django_app_organization.models import Organization
from django_mall_product.graphql.storefront.types.product import ProductNode
from django_mall_product.models import Product


class IncrementProductCountAccess(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    product = graphene.Field(ProductNode)

    @classmethod
    @transaction.atomic
    def mutate_and_get_payload(cls, root, info: ResolveInfo, **input):
        id = input["id"]

        try:
            _, product_id = from_global_id(id)
        except:
            raise Exception("Bad Request!")

        organization = Organization.objects.only("id").get(
            schema_name=connection.schema_name
        )

        try:
            product = Product.objects.get(
                organization_id=organization.id, pk=product_id
            )
            product.count_access += 1
            product.save()
        except Product.DoesNotExist:
            raise Exception("Can not find this product!")

        return IncrementProductCountAccess(success=True, product=product)


class ProductMutation(graphene.ObjectType):
    product_count_access_increment = IncrementProductCountAccess.Field()


class ProductQuery(graphene.ObjectType):
    product = graphene.relay.Node.Field(ProductNode)
    products = DjangoFilterConnectionField(
        ProductNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
