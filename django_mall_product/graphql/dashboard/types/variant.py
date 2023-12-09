from django_filters import BooleanFilter, CharFilter, FilterSet, OrderingFilter
from django_prices.models import MoneyField
from graphene import ResolveInfo
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field
from graphene_django.filter import DjangoFilterConnectionField
import graphene
import graphene_django_optimizer as gql_optimizer

from django_app_core.relay.connection import ExtendedConnection
from django_app_core.types import Money
from django_mall_product.graphql.dashboard.types.product_option_value import (
    ProductOptionValueNode,
)
from django_mall_product.models import Variant, VariantOptionValue


class VariantType(DjangoObjectType):
    class Meta:
        model = Variant
        fields = ()


@convert_django_field.register(MoneyField)
def convert_money_field_to_string(field, registry=None):
    return graphene.Field(Money)


class VariantFilter(FilterSet):
    slug = CharFilter(field_name="slug", lookup_expr="exact")
    sku = CharFilter(field_name="sku", lookup_expr="icontains")
    name = CharFilter(field_name="product__translations__name", lookup_expr="icontains")
    is_primary = BooleanFilter(field_name="is_primary")
    is_published = BooleanFilter(field_name="is_published")

    class Meta:
        model = Variant
        fields = []

    order_by = OrderingFilter(
        fields=(
            ("product__sort_key", "sort_key"),
            "price_sale_amount",
            "created_at",
            "updated_at",
        )
    )


class VariantConnection(graphene.relay.Connection):
    class Meta:
        node = VariantType


class VariantNode(gql_optimizer.OptimizedDjangoObjectType):
    class Meta:
        model = Variant
        exclude = (
            "currency",
            "price_amount",
            "price_sale_amount",
            "deleted",
            "deleted_by_cascade",
        )
        filterset_class = VariantFilter
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    selected_option_values = DjangoFilterConnectionField(
        ProductOptionValueNode, orderBy=graphene.List(of_type=graphene.String)
    )

    @classmethod
    def get_queryset(cls, queryset, info: ResolveInfo):
        return queryset.select_related("product").prefetch_related(
            "selected_option_values"
        )

    @classmethod
    def get_node(cls, info: ResolveInfo, id):
        try:
            variant = cls._meta.model.objects.select_related("product").get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        return variant

    @gql_optimizer.resolver_hints(select_related=("selected_option_values",))
    @staticmethod
    def resolve_selected_option_values(root: Variant, info: ResolveInfo):
        idList = (
            VariantOptionValue.objects.filter(variant=root)
            .filter(deleted__isnull=True)
            .values_list("product_option_value_id", flat=True)
        )
        return root.selected_option_values.filter(id__in=idList)
