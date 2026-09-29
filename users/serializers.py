from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Профиль пользователя: чтение и редактирование своих данных."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 'image')
        # Роль меняется только администратором через админку: иначе любой
        # желающий выдал бы себе права админа обычным PATCH на свой профиль
        read_only_fields = ('id', 'role')


class UserRegisterSerializer(BaseUserCreateSerializer):
    """Регистрация. Базовый сериализатор Djoser уже проверяет пароль
    валидаторами Django и хеширует его — своё повторять не нужно."""

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'phone')
