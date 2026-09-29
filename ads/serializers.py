from rest_framework import serializers

from ads.models import Ad, Review


class AdSerializer(serializers.ModelSerializer):
    """Объявление в списке и при создании.

    Автор не приходит из запроса — он берётся из токена во вьюхе.
    Иначе можно было бы создать объявление от чужого имени, подставив
    чужой id в теле запроса.
    """

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ad
        fields = ('id', 'title', 'price', 'description', 'author', 'created_at')
        read_only_fields = ('id', 'author', 'created_at')


class AdDetailSerializer(AdSerializer):
    """Карточка объявления: то же плюс контакты продавца.

    Телефон и имя показываем только на детальной странице, а она
    закрыта авторизацией. В общем списке контактов нет — иначе
    их собрал бы любой робот одним запросом.
    """

    author_first_name = serializers.CharField(source='author.first_name', read_only=True)
    author_last_name = serializers.CharField(source='author.last_name', read_only=True)
    author_phone = serializers.CharField(source='author.phone', read_only=True)
    reviews_count = serializers.IntegerField(source='reviews.count', read_only=True)

    class Meta(AdSerializer.Meta):
        fields = AdSerializer.Meta.fields + (
            'author_first_name',
            'author_last_name',
            'author_phone',
            'reviews_count',
        )


class ReviewSerializer(serializers.ModelSerializer):
    """Отзыв под объявлением.

    Ни автор, ни объявление не принимаются из тела запроса: автор —
    это владелец токена, а объявление определяется адресом
    /ads/<id>/comments/. Так отзыв нельзя приписать чужому объявлению.
    """

    author = serializers.PrimaryKeyRelatedField(read_only=True)
    ad = serializers.PrimaryKeyRelatedField(read_only=True)
    author_first_name = serializers.CharField(source='author.first_name', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'author_first_name', 'ad', 'created_at')
        read_only_fields = ('id', 'author', 'ad', 'created_at')
