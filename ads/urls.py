from rest_framework.routers import DefaultRouter

from ads.views import AdViewSet, ReviewViewSet

router = DefaultRouter()
router.register('ads', AdViewSet, basename='ad')
# Отзывы вложены в объявление: /ads/<ad_pk>/comments/.
# Регулярное выражение прямо в префиксе избавляет от отдельной
# библиотеки для вложенных роутеров — ради одного уровня она избыточна
router.register(r'ads/(?P<ad_pk>\d+)/comments', ReviewViewSet, basename='review')

urlpatterns = router.urls
