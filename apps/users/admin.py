from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserPreference


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_suspended', 'date_joined']
    list_filter = ['role', 'is_active', 'is_suspended', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'institution']
    ordering = ['email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LMS Info', {
            'fields': ('role', 'bio', 'avatar', 'phone', 'city', 'country',
                       'timezone', 'lang', 'idnumber', 'department', 'institution', 'is_suspended'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LMS Info', {
            'fields': ('email', 'first_name', 'last_name', 'role'),
        }),
    )


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'value']
    search_fields = ['user__email', 'name']
