import graphene

from django_app_core.relay.connection import DjangoFilterConnectionField
from django_mall_product.graphql.storefront.types.variant import VariantNode


class VariantMutation(graphene.ObjectType):
    pass


class VariantQuery(graphene.ObjectType):
    variant = graphene.relay.Node.Field(VariantNode)
    variants = DjangoFilterConnectionField(
        VariantNode,
        orderBy=graphene.List(of_type=graphene.String),
        page_number=graphene.Int(),
        page_size=graphene.Int(),
    )
