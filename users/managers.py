from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер пользователей, у которых вместо логина email.

    Стандартный UserManager Django требует username и падает без него.
    Здесь та же логика, но ключ — email, и он приводится к нормальному
    виду: домен в нижний регистр, чтобы Ivan@Mail.ru и ivan@mail.ru
    не стали двумя разными аккаунтами.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email обязателен: он используется как логин')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Суперпользователь в админке и роль admin в API — разные вещи.
        # Синхронизируем их, иначе созданный через createsuperuser человек
        # не получит админских прав в самом API
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('У суперпользователя должно быть is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('У суперпользователя должно быть is_superuser=True')

        return self._create_user(email, password, **extra_fields)
