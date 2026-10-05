from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class UserRole(models.TextChoices):
    """Ролей ровно две, как в задании. TextChoices вместо строк —
    чтобы опечатка 'admn' не прошла молча в базу."""

    USER = 'user', 'Пользователь'
    ADMIN = 'admin', 'Администратор'


class User(AbstractUser):
    """Пользователь сайта объявлений.

    От AbstractUser берём готовые пароли, права и флаги активности,
    но выбрасываем username: входят по email.
    """

    # None, а не удаление поля: так Django понимает, что колонки быть не должно
    username = None

    first_name = models.CharField(
        max_length=64, blank=True, verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=64, blank=True, verbose_name='Фамилия'
    )
    phone = models.CharField(
        max_length=32, blank=True, verbose_name='Телефон для связи'
    )
    email = models.EmailField(
        unique=True, verbose_name='Email', help_text='Используется как логин'
    )
    role = models.CharField(
        max_length=5,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name='Роль',
    )
    image = models.ImageField(
        upload_to='avatars/', blank=True, null=True, verbose_name='Аватарка'
    )

    # Django спрашивает это поле при входе и при createsuperuser
    USERNAME_FIELD = 'email'
    # Что ещё спросить в createsuperuser кроме email и пароля.
    # Пусто: имя и телефон человек заполнит в профиле сам
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.email

    @property
    def is_admin(self) -> bool:
        """Админ по роли. Отдельно от is_superuser: суперпользователь —
        это про админку Django, а role — про права в API."""
        return self.role == UserRole.ADMIN
