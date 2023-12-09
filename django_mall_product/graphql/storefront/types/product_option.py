import datetime

from django.db.models import Q

from django_filters import CharFilter, FilterSet, OrderingFilter
from graphene import ResolveInfo
from graphene_django import DjangoListField, DjangoObjectType
import graphene
import graphene_django_optimizer as gql_optimizer

from django_app_core.relay.connection import ExtendedConnection
from django_mall_product.models import ProductOption, ProductOptionTrans


class ProductOptionType(DjangoObjectType):
    class Meta:
        model = ProductOption
        fields = ()


class ProductOptionTransType(DjangoObjectType):
    class Meta:
        model = ProductOptionTrans
        fields = (
            "language_code",
            "name",
        )


class ProductOptionFilter(FilterSet):
    name = CharFilter(field_name="translations__name", lookup_expr="icontains")

    class Meta:
        model = ProductOption
        fields = []

    order_by = OrderingFilter(fields=("sort_key",))


class ProductOptionConnection(graphene.relay.Connection):
    class Meta:
        node = ProductOptionType


class ProductOptionNode(gql_optimizer.OptimizedDjangoObjectType):
    class Meta:
        model = ProductOption
        exclude = (
            "deleted",
            "deleted_by_cascade",
        )
        filterset_class = ProductOptionFilter
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    translations = DjangoListField(ProductOptionTransType)

    @classmethod
    def get_queryset(cls, queryset, info: ResolveInfo):
        return (
            queryset.select_related("product", "product__organization")
            .prefetch_related(
                "translations",
                "productoptionvalue_set",
                "productoptionvalue_set__translations",
            )
            .filter(
                Q(product__published_at__lte=datetime.date.today())
                | Q(product__published_at__isnull=True),
                product__is_published=True,
                product__can_search=True,
            )
        )

    @classmethod
    def get_node(cls, info: ResolveInfo, id):
        try:
            product_option = (
                cls._meta.model.objects.select_related(
                    "product", "product__organization"
                )
                .filter(
                    Q(product__published_at__lte=datetime.date.today())
                    | Q(product__published_at__isnull=True),
                    product__is_published=True,
                    product__can_search=True,
                )
                .get(pk=id)
            )
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        return product_option

    @staticmethod
    def resolve_translations(root: ProductOption, info: ResolveInfo):
        return root.translations
