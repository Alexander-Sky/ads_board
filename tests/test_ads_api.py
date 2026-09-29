"""API объявлений: доступ, CRUD, поиск, пагинация.

Главное здесь — матрица прав из ТЗ. Анониму открыт только список;
всё остальное требует авторизации, а изменять и удалять можно
лишь своё, если ты не администратор.
"""

import pytest
from rest_framework import status

from ads.models import Ad


@pytest.mark.django_db
class TestAdAccess:

    def test_anonymous_sees_list(self, api_client, ad):
        """Единственное, что открыто без токена."""
        response = api_client.get('/ads/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_anonymous_cannot_see_one_ad(self, api_client, ad):
        """Карточка закрыта: в ней контакты продавца."""
        response = api_client.get(f'/ads/{ad.pk}/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_anonymous_cannot_create(self, api_client):
        response = api_client.post('/ads/', {'title': 'Стол', 'price': 100})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Ad.objects.count() == 0

    def test_user_sees_one_ad(self, auth_client, ad):
        response = auth_client.get(f'/ads/{ad.pk}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Велосипед'
        # На карточке видны контакты продавца
        assert 'author_phone' in response.data


@pytest.mark.django_db
class TestAdCreate:

    def test_user_creates_ad(self, auth_client, user):
        response = auth_client.post(
            '/ads/', {'title': 'Стол', 'price': 3000, 'description': 'Дубовый'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Ad.objects.count() == 1
        assert Ad.objects.first().author == user

    def test_author_taken_from_token_not_from_body(self, auth_client, user, other_user):
        """Подставить чужой id в тело запроса не получится:
        автор всегда берётся из токена."""
        response = auth_client.post(
            '/ads/', {'title': 'Стол', 'price': 3000, 'author': other_user.pk}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Ad.objects.first().author == user

    def test_price_cannot_be_negative(self, auth_client):
        response = auth_client.post('/ads/', {'title': 'Стол', 'price': -100})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdEditAndDelete:

    def test_author_edits_own_ad(self, auth_client, ad):
        response = auth_client.patch(f'/ads/{ad.pk}/', {'price': 12000})

        assert response.status_code == status.HTTP_200_OK
        ad.refresh_from_db()
        assert ad.price == 12000

    def test_stranger_cannot_edit(self, api_client, other_user, ad):
        api_client.force_authenticate(user=other_user)

        response = api_client.patch(f'/ads/{ad.pk}/', {'price': 1})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        ad.refresh_from_db()
        assert ad.price == 15000

    def test_stranger_cannot_delete(self, api_client, other_user, ad):
        api_client.force_authenticate(user=other_user)

        response = api_client.delete(f'/ads/{ad.pk}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Ad.objects.count() == 1

    def test_author_deletes_own_ad(self, auth_client, ad):
        response = auth_client.delete(f'/ads/{ad.pk}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Ad.objects.count() == 0

    def test_admin_edits_any_ad(self, admin_client, ad):
        """Права администратора из ТЗ: он может всё и с чужим."""
        response = admin_client.patch(f'/ads/{ad.pk}/', {'price': 999})

        assert response.status_code == status.HTTP_200_OK
        ad.refresh_from_db()
        assert ad.price == 999

    def test_admin_deletes_any_ad(self, admin_client, ad):
        response = admin_client.delete(f'/ads/{ad.pk}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Ad.objects.count() == 0


@pytest.mark.django_db
class TestAdListBehaviour:

    def test_four_per_page(self, api_client, user):
        """Требование ТЗ: не больше четырёх объявлений на странице."""
        for i in range(6):
            Ad.objects.create(title=f'Товар {i}', price=100 + i, author=user)

        response = api_client.get('/ads/')

        assert response.data['count'] == 6
        assert len(response.data['results']) == 4
        assert response.data['next'] is not None

    def test_page_size_cannot_be_overridden(self, api_client, user):
        """?page_size=100 не должен обходить ограничение."""
        for i in range(6):
            Ad.objects.create(title=f'Товар {i}', price=100, author=user)

        response = api_client.get('/ads/?page_size=100')

        assert len(response.data['results']) == 4

    def test_newest_first(self, api_client, user):
        Ad.objects.create(title='Старое', price=100, author=user)
        newest = Ad.objects.create(title='Новое', price=200, author=user)

        response = api_client.get('/ads/')

        assert response.data['results'][0]['id'] == newest.pk

    def test_search_by_title(self, api_client, user):
        Ad.objects.create(title='Велосипед горный', price=15000, author=user)
        Ad.objects.create(title='Стол письменный', price=3000, author=user)

        response = api_client.get('/ads/?title=велос')

        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Велосипед горный'

    def test_search_ignores_case(self, api_client, user):
        Ad.objects.create(title='Велосипед горный', price=15000, author=user)

        response = api_client.get('/ads/?title=ВЕЛОСИПЕД')

        assert response.data['count'] == 1

    def test_list_hides_seller_contacts(self, api_client, ad):
        """В общем списке телефона быть не должно — иначе его
        соберёт любой робот одним запросом."""
        response = api_client.get('/ads/')

        assert 'author_phone' not in response.data['results'][0]


@pytest.mark.django_db
class TestMyAds:

    def test_returns_only_own_ads(self, auth_client, user, other_user):
        Ad.objects.create(title='Моё', price=100, author=user)
        Ad.objects.create(title='Чужое', price=200, author=other_user)

        response = auth_client.get('/ads/me/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Моё'

    def test_anonymous_denied(self, api_client):
        response = api_client.get('/ads/me/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
