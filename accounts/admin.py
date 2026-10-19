from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour le modèle User"""
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'bio', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'bio', 'avatar')}),
    )
