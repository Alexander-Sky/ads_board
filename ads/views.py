from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from ads.filters import AdFilter
from ads.models import Ad, Review
from ads.paginators import AdPagination
from ads.permissions import IsAuthorOrAdmin
from ads.serializers import AdDetailSerializer, AdSerializer, ReviewSerializer


@extend_schema_view(
    list=extend_schema(
        summary='Список объявлений',
        description='Доступен без авторизации. По четыре на страницу, новые сверху. '
                    'Поиск по названию: ?title=велосипед',
    ),
    retrieve=extend_schema(summary='Одно объявление с контактами продавца'),
    create=extend_schema(summary='Создать объявление'),
    update=extend_schema(summary='Заменить своё объявление'),
    partial_update=extend_schema(summary='Изменить своё объявление'),
    destroy=extend_schema(summary='Удалить своё объявление'),
)
class AdViewSet(ModelViewSet):
    """CRUD объявлений.

    Права разные на разные действия, поэтому они собираются
    в get_permissions, а не задаются одним списком на весь класс.
    """

    # select_related убирает отдельный запрос к пользователю на каждое
    # объявление: без него список из четырёх объявлений — пять запросов
    queryset = Ad.objects.select_related('author').all()
    pagination_class = AdPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AdFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdDetailSerializer
        return AdSerializer

    def get_permissions(self):
        if self.action == 'list':
            # Единственное, что открыто анониму: витрина объявлений
            self.permission_classes = (AllowAny,)
        elif self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = (IsAuthenticated, IsAuthorOrAdmin)
        else:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(summary='Мои объявления')
    @action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def me(self, request):
        """Объявления текущего пользователя.

        Отдельный адрес, а не фильтр ?author=<id>: так нельзя случайно
        (или намеренно) запросить чужой список по чужому id.
        """
        queryset = self.filter_queryset(self.get_queryset().filter(author=request.user))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary='Отзывы под объявлением'),
    retrieve=extend_schema(summary='Один отзыв'),
    create=extend_schema(summary='Оставить отзыв'),
    update=extend_schema(summary='Заменить свой отзыв'),
    partial_update=extend_schema(summary='Изменить свой отзыв'),
    destroy=extend_schema(summary='Удалить свой отзыв'),
)
class ReviewViewSet(ModelViewSet):
    """Отзывы, вложенные в объявление: /ads/<ad_pk>/comments/"""

    serializer_class = ReviewSerializer
    # Пустая выборка нужна только генератору документации: настоящая
    # приходит из get_queryset, но там есть ad_pk из адреса, которого
    # при построении схемы не существует. Без этой строки drf-spectacular
    # не может определить модель и выдаёт предупреждения
    queryset = Review.objects.none()

    def get_queryset(self):
        # Выборка всегда ограничена одним объявлением из адреса.
        # Поэтому по чужому id отзыв не достать даже случайно
        return (
            Review.objects
            .filter(ad_id=self.kwargs['ad_pk'])
            .select_related('author', 'ad')
        )

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = (IsAuthenticated, IsAuthorOrAdmin)
        else:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def perform_create(self, serializer):
        # Объявление берётся из адреса, а не из тела запроса.
        # Нет такого объявления — честный 404, а не отзыв в пустоту
        ad = get_object_or_404(Ad, pk=self.kwargs['ad_pk'])
        serializer.save(author=self.request.user, ad=ad)
