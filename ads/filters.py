from django_filters import rest_framework as filters

from ads.models import Ad


class AdFilter(filters.FilterSet):
    """Поиск объявлений по названию.

    icontains, а не exact: человек в строке поиска пишет «велос»,
    а не полное название товара. И регистр его волновать не должен.
    """

    title = filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Поиск по названию товара',
    )

    class Meta:
        model = Ad
        fields = ('title',)
