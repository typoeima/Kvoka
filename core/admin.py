from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FocusSession, WorkspaceConfig, Achievement, EarnedAchievement

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Квока профиль', {'fields': ('avatar', 'rank', 'total_hours', 'current_days', 'max_days')}),
    )
    list_display = ('username', 'email', 'rank', 'total_hours', 'current_days', 'max_days')

admin.site.register(User, CustomUserAdmin)
admin.site.register(FocusSession)
admin.site.register(WorkspaceConfig)
admin.site.register(Achievement)
admin.site.register(EarnedAchievement)