"""Общие фикстуры для всех тестов.

pytest подхватывает этот файл автоматически — импортировать его не нужно.
Здесь живут заготовки, которые иначе пришлось бы повторять в каждом тесте:
клиент API, пользователи с разными ролями, объявление и отзыв.
"""

import pytest
from rest_framework.test import APIClient

from ads.models import Ad, Review
from users.models import User, UserRole


@pytest.fixture
def api_client():
    """Клиент без авторизации — им проверяем доступ анонима."""
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='user@example.com',
        password='Str0ngPass!42',
        first_name='Иван',
    )


@pytest.fixture
def other_user(db):
    """Второй обычный пользователь: нужен, чтобы проверить, что чужое
    объявление редактировать нельзя. Без него такой тест не написать."""
    return User.objects.create_user(
        email='other@example.com',
        password='Str0ngPass!42',
        first_name='Пётр',
    )


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email='admin@example.com',
        password='Str0ngPass!42',
        role=UserRole.ADMIN,
    )


@pytest.fixture
def auth_client(api_client, user):
    """Клиент, авторизованный обычным пользователем."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin):
    api_client.force_authenticate(user=admin)
    return api_client


@pytest.fixture
def ad(user):
    return Ad.objects.create(
        title='Велосипед',
        price=15000,
        description='Почти новый, катались одно лето',
        author=user,
    )


@pytest.fixture
def review(user, ad):
    return Review.objects.create(text='Отличный товар', author=user, ad=ad)
