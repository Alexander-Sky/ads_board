from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAuthorOrAdmin(BasePermission):
    """Изменять и удалять объект может только его автор или администратор.

    Проверка объектная: она срабатывает после того, как объект найден.
    Поэтому её всегда ставят рядом с IsAuthenticated — сама по себе
    она пропустила бы анонима, у которого объекта просто нет.
    """

    message = 'Изменять и удалять можно только свои записи'

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        user = request.user
        # getattr, а не user.is_admin: у AnonymousUser такого свойства нет,
        # и обращение к нему упало бы с AttributeError вместо честного 403
        return obj.author == user or getattr(user, 'is_admin', False)
