import graphene

from django_app_core.relay.connection import DjangoFilterConnectionField
from django_mall_product.graphql.storefront.types.product_option_value import (
    ProductOptionValueNode,
)


class ProductOptionValueMutation(graphene.ObjectType):
    pass


class ProductOptionValueQuery(graphene.ObjectType):
    product_option_value = graphene.relay.Node.Field(ProductOptionValueNode)
    product_option_values = DjangoFilterConnectionField(
        ProductOptionValueNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
