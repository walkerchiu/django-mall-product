import graphene

from django_mall_product.graphql.website.product import ProductQuery


class Mutation(
    graphene.ObjectType,
):
    pass


class Query(
    ProductQuery,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(mutation=Mutation, query=Query)
