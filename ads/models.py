from django.conf import settings
from django.db import models


class Ad(models.Model):
    """Объявление о продаже товара."""

    title = models.CharField(max_length=200, verbose_name='Название товара')
    price = models.PositiveIntegerField(verbose_name='Цена, ₽')
    description = models.TextField(blank=True, verbose_name='Описание товара')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ads',
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        # Требование ТЗ: чем новее объявление, тем выше. Сортировка задана
        # здесь, а не во вьюхе, — иначе её пришлось бы дублировать в каждой
        # выборке, и пагинация без явного порядка выдавала бы дубли
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.title} — {self.price} ₽'


class Review(models.Model):
    """Отзыв под объявлением."""

    text = models.TextField(verbose_name='Текст отзыва')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
    )
    ad = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Объявление',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Отзыв {self.author} к «{self.ad.title}»'
