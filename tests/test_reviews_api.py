"""API отзывов: /ads/<ad_pk>/comments/

Отзывы вложены в объявление, поэтому отдельно проверяем, что выборка
не «протекает» между объявлениями и что отзыв нельзя приписать чужому.
"""

import pytest
from rest_framework import status

from ads.models import Ad, Review


@pytest.mark.django_db
class TestReviewAccess:

    def test_anonymous_cannot_see_reviews(self, api_client, ad, review):
        response = api_client.get(f'/ads/{ad.pk}/comments/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_anonymous_cannot_create(self, api_client, ad):
        response = api_client.post(f'/ads/{ad.pk}/comments/', {'text': 'Спам'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Review.objects.count() == 0

    def test_user_sees_reviews(self, auth_client, ad, review):
        response = auth_client.get(f'/ads/{ad.pk}/comments/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['text'] == 'Отличный товар'


@pytest.mark.django_db
class TestReviewCreate:

    def test_user_leaves_review(self, auth_client, user, ad):
        response = auth_client.post(f'/ads/{ad.pk}/comments/', {'text': 'Беру'})

        assert response.status_code == status.HTTP_201_CREATED
        created = Review.objects.get()
        assert created.author == user
        assert created.ad == ad

    def test_ad_taken_from_url(self, auth_client, user, ad):
        """Объявление определяется адресом, а не телом запроса:
        приписать отзыв к чужому объявлению нельзя."""
        other_ad = Ad.objects.create(title='Другое', price=1, author=user)

        response = auth_client.post(
            f'/ads/{ad.pk}/comments/', {'text': 'Беру', 'ad': other_ad.pk}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Review.objects.get().ad == ad

    def test_review_for_missing_ad_is_404(self, auth_client):
        response = auth_client.post('/ads/9999/comments/', {'text': 'В пустоту'})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_text_rejected(self, auth_client, ad):
        response = auth_client.post(f'/ads/{ad.pk}/comments/', {'text': ''})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReviewEditAndDelete:

    def test_author_edits_own_review(self, auth_client, ad, review):
        response = auth_client.patch(
            f'/ads/{ad.pk}/comments/{review.pk}/', {'text': 'Передумал'}
        )

        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.text == 'Передумал'

    def test_stranger_cannot_edit(self, api_client, other_user, ad, review):
        api_client.force_authenticate(user=other_user)

        response = api_client.patch(
            f'/ads/{ad.pk}/comments/{review.pk}/', {'text': 'Взлом'}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_author_deletes_own_review(self, auth_client, ad, review):
        response = auth_client.delete(f'/ads/{ad.pk}/comments/{review.pk}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Review.objects.count() == 0

    def test_admin_deletes_any_review(self, admin_client, ad, review):
        """Администратор модерирует чужие отзывы — требование ТЗ."""
        response = admin_client.delete(f'/ads/{ad.pk}/comments/{review.pk}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Review.objects.count() == 0


@pytest.mark.django_db
class TestReviewIsolation:

    def test_reviews_do_not_leak_between_ads(self, auth_client, user, ad, review):
        """Отзыв одного объявления не должен появляться под другим."""
        other_ad = Ad.objects.create(title='Другое', price=1, author=user)

        response = auth_client.get(f'/ads/{other_ad.pk}/comments/')

        assert len(response.data) == 0

    def test_review_of_another_ad_is_not_reachable(self, auth_client, user, ad, review):
        """По адресу чужого объявления свой отзыв тоже не достать."""
        other_ad = Ad.objects.create(title='Другое', price=1, author=user)

        response = auth_client.get(f'/ads/{other_ad.pk}/comments/{review.pk}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
