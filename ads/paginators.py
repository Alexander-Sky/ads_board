from rest_framework.pagination import PageNumberPagination


class AdPagination(PageNumberPagination):
    """Пагинация списка объявлений.

    Требование ТЗ — не более четырёх объектов на странице. Размер
    намеренно не даём переопределять параметром запроса: иначе
    ?page_size=1000 обошёл бы ограничение одним запросом.
    """

    page_size = 4
