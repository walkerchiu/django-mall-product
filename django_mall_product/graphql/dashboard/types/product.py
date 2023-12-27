from django.db.models import Max, Min

from django_filters import (
    BooleanFilter,
    CharFilter,
    DateTimeFilter,
    FilterSet,
    OrderingFilter,
)
from graphene import ResolveInfo
from graphene_django import DjangoListField, DjangoObjectType
from graphql_jwt.decorators import login_required
import graphene

from django_app_core.relay.connection import ExtendedConnection
from django_app_core.types import TransTypeInput
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
            "description",
            "summary",
            "content",
        )


class ProductTransInput(TransTypeInput):
    name = graphene.String()
    description = graphene.String()
    summary = graphene.String()
    content = graphene.String()


class ProductFilter(FilterSet):
    language_code = CharFilter(
        field_name="translations__language_code", lookup_expr="exact"
    )
    name = CharFilter(field_name="translations__name", lookup_expr="icontains")
    description = CharFilter(
        field_name="translations__description", lookup_expr="icontains"
    )
    summary = CharFilter(field_name="translations__summary", lookup_expr="icontains")
    content = CharFilter(field_name="translations__content", lookup_expr="icontains")
    slug = CharFilter(field_name="slug", lookup_expr="exact")
    serial = CharFilter(field_name="serial", lookup_expr="exact")
    can_search = BooleanFilter(field_name="can_search")
    is_published = BooleanFilter(field_name="is_published")
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

    def filter_order_by(self, queryset, name, value):
        annotations = {}
        order_fields = []

        for field in value:
            clean_field = field.replace("-", "")

            if clean_field == "price_sale_amount":
                annotations["max_price"] = Max("variant__price_sale_amount")
                annotations["min_price"] = Min("variant__price_sale_amount")

                if "-" in field:
                    order_fields.append("-max_price")
                else:
                    order_fields.append("min_price")
            else:
                order_fields.append(field)

        if annotations:
            queryset = queryset.annotate(**annotations)

        if order_fields:
            queryset = queryset.order_by(*order_fields)

        return queryset

    order_by = OrderingFilter(
        fields=(
            ("translations__name", "name"),
            "sort_key",
            "count_access",
            "count_add_to_cart",
            "created_at",
            "updated_at",
        ),
        method="filter_order_by",
    )


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        exclude = (
            "deleted",
            "deleted_by_cascade",
        )
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection

    translation = graphene.Field(ProductTransType)
    translations = DjangoListField(ProductTransType)

    @classmethod
    @login_required
    def get_queryset(cls, queryset, info: ResolveInfo):
        return queryset.prefetch_related(
            "translations",
            "variant_set",
            "variant_set__selected_option_values",
            "productoption_set__translations",
            "productoption_set__productoptionvalue_set",
            "productoption_set__productoptionvalue_set__translations",
        )

    @classmethod
    @login_required
    def get_node(cls, info: ResolveInfo, id):
        try:
            product = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise Exception("Bad Request!")

        return product

    @staticmethod
    def resolve_translation(root: Product, info: ResolveInfo):
        return root.translations.filter(language_code=root.language_code).first()

    @staticmethod
    def resolve_translations(root: Product, info: ResolveInfo):
        return root.translations


class ProductConnection(graphene.relay.Connection):
    class Meta:
        node = ProductType
