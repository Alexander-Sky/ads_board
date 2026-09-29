"""
Настройки проекта «Доска объявлений».

Всё, что меняется между машиной разработчика и сервером, читается из
переменных окружения. Ни одного секрета в коде: файл .env в репозиторий
не попадает, а рядом лежит .env.template с описанием каждой переменной.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Читаем .env, если он есть. В Docker переменные приходят из compose,
# и тогда файла может не быть — это нормально
load_dotenv(BASE_DIR / '.env')


def env_bool(name: str, default: bool = False) -> bool:
    """Переменные окружения всегда строки: 'False' — это непустая строка,
    и в булевом контексте она истинна. Поэтому сравниваем явно."""
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name: str, default: str = '') -> list[str]:
    """Список через запятую: 'a, b ,c' -> ['a', 'b', 'c']. Пустые куски
    отбрасываем, иначе лишняя запятая в .env добавит пустой домен."""
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-only-for-local-development')

DEBUG = env_bool('DEBUG', True)

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
    'djoser',

    # Свои
    'users',
    'ads',
]

MIDDLEWARE = [
    # CorsMiddleware должен стоять как можно выше и обязательно ВЫШЕ
    # CommonMiddleware: иначе на часть ответов заголовки CORS не попадут
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- База данных ---
# PostgreSQL по требованию задания. Параметры те же, что читает контейнер
# с базой, — так значение задаётся в одном месте, в .env
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'ads_board'),
        'USER': os.getenv('DB_USER', 'ads_board'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = os.getenv('TIME_ZONE', 'Europe/Vienna')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Логин по email, а не по имени пользователя — так требует задание
AUTH_USER_MODEL = 'users.User'

# --- DRF ---
REST_FRAMEWORK = {
    # По умолчанию API закрыто. Там, где нужен анонимный доступ
    # (список объявлений), разрешение выдаётся точечно во вьюхе.
    # Обратный подход — открыть всё и закрывать по одному — опаснее:
    # забытая вьюха останется публичной
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# --- JWT ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('ACCESS_TOKEN_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('REFRESH_TOKEN_DAYS', '1'))),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- Djoser ---
# Регистрация и сброс пароля через почту. Адреса эндпоинтов заданы
# библиотекой и совпадают с требованиями ТЗ: /users/reset_password/
# и /users/reset_password_confirm/
DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': False,
    'SEND_ACTIVATION_EMAIL': False,
    # Шаблон ссылки, которая уходит пользователю на почту. Фронтенд
    # подставляет uid и token в форму и отправляет их на confirm-эндпоинт
    'PASSWORD_RESET_CONFIRM_URL': os.getenv(
        'PASSWORD_RESET_CONFIRM_URL', 'password/reset/confirm/{uid}/{token}'
    ),
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': False,
    'SERIALIZERS': {
        'user': 'users.serializers.UserSerializer',
        'current_user': 'users.serializers.UserSerializer',
        'user_create': 'users.serializers.UserRegisterSerializer',
    },
}

# --- Почта ---
# В Django 6.1 настройки EMAIL_* объявлены устаревшими и заменены на MAILERS.
# Попытка использовать старые вместе с новыми роняет проект на старте:
# ImproperlyConfigured: Deprecated email settings are not allowed when MAILERS
# is defined. Поэтому здесь только MAILERS.
#
# По умолчанию письма печатаются в консоль — удобно при разработке,
# видно ссылку для сброса пароля и не нужен почтовый сервер.
EMAIL_MODE = os.getenv('EMAIL_MODE', 'console')

if EMAIL_MODE == 'smtp':
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': os.getenv('EMAIL_HOST', ''),
                'port': int(os.getenv('EMAIL_PORT', '587')),
                'username': os.getenv('EMAIL_HOST_USER', ''),
                'password': os.getenv('EMAIL_HOST_PASSWORD', ''),
                'use_tls': env_bool('EMAIL_USE_TLS', True),
            },
        }
    }
else:
    MAILERS = {
        'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'},
    }

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ads-board.local')

# --- CORS ---
# Фронтенд живёт на другом домене, и без явного списка браузер
# заблокирует его запросы к API
CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'
)
CSRF_TRUSTED_ORIGINS = env_list(
    'CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'
)

# --- Документация API ---
SPECTACULAR_SETTINGS = {
    'TITLE': 'Доска объявлений API',
    'DESCRIPTION': 'Backend сайта объявлений: пользователи, объявления, отзывы',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
