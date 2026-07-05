from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    ordering = ['email']
    list_display = ['email', 'nome', 'is_staff', 'is_active']
    search_fields = ['email', 'nome']
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('nome',)}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')
