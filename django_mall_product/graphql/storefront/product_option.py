import graphene

from django_app_core.relay.connection import DjangoFilterConnectionField
from django_mall_product.graphql.storefront.types.product_option import (
    ProductOptionNode,
)


class ProductOptionMutation(graphene.ObjectType):
    pass


class ProductOptionQuery(graphene.ObjectType):
    product_option = graphene.relay.Node.Field(ProductOptionNode)
    product_options = DjangoFilterConnectionField(
        ProductOptionNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
