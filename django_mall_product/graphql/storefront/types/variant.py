import datetime

from django.db.models import Q

from django_filters import BooleanFilter, CharFilter, FilterSet, OrderingFilter
from django_prices.models import MoneyField
from graphene import ResolveInfo
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field
from graphene_django.filter import DjangoFilterConnectionField
from graphql_relay import from_global_id
import graphene
import graphene_django_optimizer as gql_optimizer

from django_app_core.relay.connection import ExtendedConnection
from django_app_core.types import Money
from django_mall_product.graphql.storefront.types.product_option_value import (
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
    name = CharFilter(field_name="product__translations__name", lookup_expr="icontains")
    is_primary = BooleanFilter(field_name="is_primary")

    class Meta:
        model = Variant
        fields = []

    def filter_collection_in(self, queryset, name, value):
        idList = []
        for _id in value:
            _, collection_id = from_global_id(_id)
            idList.append(collection_id)
        return (
            queryset.filter(product__collections__in=idList)
            .filter(
                Q(product__collections__published_at__lte=datetime.date.today())
                | Q(product__collections__published_at__isnull=True),
                product__collections__is_published=True,
            )
            .distinct()
        )

    def filter_collection_not_in(self, queryset, name, value):
        idList = []
        for _id in value:
            _, collection_id = from_global_id(_id)
            idList.append(collection_id)
        return (
            queryset.exclude(product__collections__in=idList)
            .filter(
                Q(product__collections__published_at__lte=datetime.date.today())
                | Q(product__collections__published_at__isnull=True),
                product__collections__is_published=True,
            )
            .distinct()
        )

    order_by = OrderingFilter(
        fields=(
            ("product__sort_key", "sort_key"),
            ("product__count_access", "count_access"),
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
            "sku",
            "currency",
            "price_amount",
            "price_sale_amount",
            "is_published",
            "published_at",
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
        return (
            queryset.select_related("product")
            .prefetch_related("selected_option_values")
            .filter(
                Q(published_at__lte=datetime.date.today())
                | Q(published_at__isnull=True),
                is_published=True,
            )
        )

    @classmethod
    def get_node(cls, info: ResolveInfo, id):
        try:
            variant = cls._meta.model.objects.select_related("product").get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        if variant.is_visible and variant.product.is_visible:
            return variant

        raise Exception("Bad Request!")

    @gql_optimizer.resolver_hints(select_related=("selected_option_values",))
    @staticmethod
    def resolve_selected_option_values(root: Variant, info: ResolveInfo):
        idList = (
            VariantOptionValue.objects.filter(variant=root)
            .filter(deleted__isnull=True)
            .values_list("product_option_value_id", flat=True)
        )
        return root.selected_option_values.filter(id__in=idList)
