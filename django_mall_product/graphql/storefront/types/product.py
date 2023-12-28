import datetime

from django.db.models import Q

from django_filters import (
    CharFilter,
    DateTimeFilter,
    FilterSet,
    OrderingFilter,
)
from graphene import ResolveInfo
from graphene_django import DjangoListField, DjangoObjectType
import graphene

from django_app_core.relay.connection import ExtendedConnection
from django_mall_product.models import Product, ProductTrans


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ()


class ProductTransType(DjangoObjectType):
    class Meta:
        model = ProductTrans
        fields = (
            "language_code",
            "name",
            "summary",
            "content",
        )


class ProductFilter(FilterSet):
    language_code = CharFilter(
        field_name="translations__language_code", lookup_expr="exact"
    )
    name = CharFilter(field_name="translations__name", lookup_expr="icontains")
    summary = CharFilter(field_name="translations__summary", lookup_expr="icontains")
    content = CharFilter(field_name="translations__content", lookup_expr="icontains")
    slug = CharFilter(field_name="slug", lookup_expr="exact")
    created_at_gt = DateTimeFilter(field_name="created_at", lookup_expr="gt")
    created_at_gte = DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lt = DateTimeFilter(field_name="created_at", lookup_expr="lt")
    created_at_lte = DateTimeFilter(field_name="created_at", lookup_expr="lte")
    updated_at_gt = DateTimeFilter(field_name="updated_at", lookup_expr="gt")
    updated_at_gte = DateTimeFilter(field_name="updated_at", lookup_expr="gte")
    updated_at_lt = DateTimeFilter(field_name="updated_at", lookup_expr="lt")
    updated_at_lte = DateTimeFilter(field_name="updated_at", lookup_expr="lte")

    class Meta:
        model = Product
        fields = []

    order_by = OrderingFilter(
        fields=(
            ("translations__name", "name"),
            "sort_key",
            "count_access",
            "count_add_to_cart",
            "created_at",
            "updated_at",
        )
    )


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        exclude = (
            "is_published",
            "published_at",
            "can_search",
            "deleted",
            "deleted_by_cascade",
        )
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    translation = graphene.Field(ProductTransType)
    translations = DjangoListField(ProductTransType)
    is_visible = graphene.Boolean()

    @classmethod
    def get_queryset(cls, queryset, info: ResolveInfo):
        return queryset.prefetch_related(
            "translations",
            "variant_set",
            "variant_set__selected_option_values",
            "productoption_set__translations",
            "productoption_set__productoptionvalue_set",
            "productoption_set__productoptionvalue_set__translations",
        ).filter(
            Q(published_at__lte=datetime.date.today()) | Q(published_at__isnull=True),
            is_published=True,
        )

    @classmethod
    def get_node(cls, info: ResolveInfo, id):
        try:
            product = cls._meta.model.objects.filter(
                Q(published_at__lte=datetime.date.today())
                | Q(published_at__isnull=True),
                is_published=True,
            ).get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        return product

    @staticmethod
    def resolve_translation(root: Product, info: ResolveInfo):
        return root.translations.filter(language_code=root.language_code).first()

    @staticmethod
    def resolve_translations(root: Product, info: ResolveInfo):
        return root.translations

    @staticmethod
    def resolve_is_visible(root: Product, info: ResolveInfo):
        return root.is_visible


class ProductConnection(graphene.relay.Connection):
    class Meta:
        node = ProductType
