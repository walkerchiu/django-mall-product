import datetime

from django.db.models import Q

from django_filters import CharFilter, FilterSet, OrderingFilter
from graphene import ResolveInfo
from graphene_django import DjangoListField, DjangoObjectType
import graphene
import graphene_django_optimizer as gql_optimizer

from django_app_core.relay.connection import ExtendedConnection
from django_mall_product.models import ProductOptionValue, ProductOptionValueTrans


class ProductOptionValueType(DjangoObjectType):
    class Meta:
        model = ProductOptionValue
        fields = ()


class ProductOptionValueTransType(DjangoObjectType):
    class Meta:
        model = ProductOptionValueTrans
        fields = (
            "language_code",
            "name",
        )


class ProductOptionValueFilter(FilterSet):
    name = CharFilter(field_name="translations__name", lookup_expr="icontains")

    class Meta:
        model = ProductOptionValue
        fields = []

    order_by = OrderingFilter(fields=("sort_key",))


class ProductOptionValueConnection(graphene.relay.Connection):
    class Meta:
        node = ProductOptionValueType


class ProductOptionValueNode(gql_optimizer.OptimizedDjangoObjectType):
    class Meta:
        model = ProductOptionValue
        exclude = (
            "deleted",
            "deleted_by_cascade",
        )
        filterset_class = ProductOptionValueFilter
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    translations = DjangoListField(ProductOptionValueTransType)

    @classmethod
    def get_queryset(cls, queryset, info: ResolveInfo):
        return queryset.select_related(
            "product_option__product", "product_option__product__organization"
        ).filter(
            Q(product_option__product__published_at__lte=datetime.date.today())
            | Q(product_option__product__published_at__isnull=True),
            product_option__product__is_published=True,
            product_option__product__can_search=True,
        )

    @classmethod
    def get_node(cls, info: ResolveInfo, id):
        try:
            product_option_value = (
                cls._meta.model.objects.select_related(
                    "product_option__product", "product_option__product__organization"
                )
                .filter(
                    Q(product_option__product__published_at__lte=datetime.date.today())
                    | Q(product_option__product__published_at__isnull=True),
                    product_option__product__is_published=True,
                    product_option__product__can_search=True,
                )
                .get(pk=id)
            )
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        return product_option_value

    @staticmethod
    def resolve_translations(root: ProductOptionValue, info: ResolveInfo):
        return root.translations
