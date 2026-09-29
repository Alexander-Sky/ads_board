"""Тесты моделей: проверяем то, что задано требованиями ТЗ,
а не то, что и так гарантирует Django."""

import pytest

from ads.models import Ad
from users.models import User, UserRole


@pytest.mark.django_db
class TestUserModel:

    def test_email_is_login(self):
        """Логин — email, поля username в модели нет."""
        assert User.USERNAME_FIELD == 'email'
        assert not hasattr(User(), 'username') or User().username is None

    def test_default_role_is_user(self, user):
        assert user.role == UserRole.USER
        assert user.is_admin is False

    def test_admin_role(self, admin):
        assert admin.is_admin is True

    def test_email_is_normalized(self):
        """Домен приводится к нижнему регистру: иначе Ivan@Mail.ru
        и ivan@mail.ru стали бы двумя разными аккаунтами."""
        user = User.objects.create_user(email='Ivan@Mail.RU', password='Str0ngPass!42')
        assert user.email == 'Ivan@mail.ru'

    def test_superuser_gets_admin_role(self):
        """Суперпользователь из createsuperuser должен быть админом
        и в API тоже, иначе права разъезжаются."""
        boss = User.objects.create_superuser(email='boss@example.com', password='Str0ngPass!42')
        assert boss.is_superuser is True
        assert boss.is_admin is True

    def test_email_required(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='Str0ngPass!42')


@pytest.mark.django_db
class TestAdModel:

    def test_newest_first(self, user):
        """Требование ТЗ: чем новее объявление, тем выше."""
        first = Ad.objects.create(title='Первое', price=100, author=user)
        second = Ad.objects.create(title='Второе', price=200, author=user)

        assert list(Ad.objects.all()) == [second, first]

    def test_str(self, ad):
        assert 'Велосипед' in str(ad)


@pytest.mark.django_db
class TestReviewModel:

    def test_linked_to_ad_and_author(self, review, ad, user):
        assert review.ad == ad
        assert review.author == user
        assert ad.reviews.count() == 1

    def test_deleted_with_ad(self, review, ad):
        """Отзывы без объявления не нужны — удаляются каскадом."""
        ad.delete()
        assert review.__class__.objects.count() == 0
