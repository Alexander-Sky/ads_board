from django.contrib import admin

from ads.models import Ad, Review


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    # Без этого на странице списка Django делает отдельный запрос
    # к пользователю на каждое объявление
    list_select_related = ('author',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('ad', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)
    list_select_related = ('ad', 'author')
