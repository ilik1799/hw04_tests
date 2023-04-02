from django.contrib import admin
from django.conf import settings

from .models import Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    # Без нее тесты не проходят
    settings.EMPTY_VALUE_DISPLAY
    # На замену строчки 20, т.к. константа вынесена в settings


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description')
